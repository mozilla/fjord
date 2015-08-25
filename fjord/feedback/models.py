from datetime import datetime, timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _lazy

import elasticsearch_dsl as es_dsl
from product_details import product_details
from rest_framework import serializers
from statsd import statsd

from fjord.base.browsers import parse_ua
from fjord.base.data import register_purger
from fjord.base.domain import get_domain
from fjord.base.models import ModelBase, JSONObjectField, EnhancedURLField
from fjord.base.utils import smart_truncate, instance_to_key, is_url
from fjord.feedback.config import (
    CODE_TO_COUNTRY,
    ANALYSIS_STOPWORDS,
    TRUNCATE_LENGTH
)
from fjord.feedback.utils import compute_grams
from fjord.search.index import (
    FjordDocType,
    FjordDocTypeManager,
    get_index_name,
    index_chunk,
    register_doctype
)
from fjord.search.tasks import register_live_index
from fjord.translations.models import get_translation_system_choices
from fjord.translations.tasks import register_auto_translation


class ProductManager(models.Manager):
    def public(self):
        """Returns publicly visible products"""
        return self.filter(on_dashboard=True)

    def from_slug(self, slug):
        return self.get(slug=slug)

    def get_product_map(self):
        products = self.filter(enabled=True).values_list('slug', 'db_name')
        return dict(list(products))


class Product(ModelBase):
    """Represents a product we capture feedback for"""
    # Whether or not this product is enabled
    enabled = models.BooleanField(default=True)

    # Used internally for notes to make it easier to manage products
    notes = models.CharField(max_length=255, blank=True, default=u'')

    # l10n: This is the name we display everywhere
    display_name = models.CharField(max_length=50)

    # l10n: This is the description on the product picker
    display_description = models.TextField(
        default=u'', blank=True,
        help_text=(u'Displayed description of the product. This will be '
                   u'localized. Should be short.')
    )

    # We're not using foreign keys, so when we save something to the
    # database, we use this name
    db_name = models.CharField(max_length=50)

    # This is the slug used in the feedback product urls; we don't use
    # the SlugField because we don't require slugs be unique
    slug = models.CharField(max_length=50)

    # Whether or not this product shows up on the dashboard; we sort of
    # use this to denote whether data is publicly available, too
    on_dashboard = models.BooleanField(default=True)

    # Whether or not this product shows up in the product picker
    on_picker = models.BooleanField(default=True)

    # The image we use on the product picker. This has to be a valid
    # image in fjord/feedback/static/img/ and should be a .png of
    # size 295x285.
    # FIXME: Make this more flexible.
    image_file = models.CharField(max_length=100, null=True, blank=True,
                                  default=u'noimage.png')

    # System slated for automatic translation, or null if none;
    # See translation app for details.
    translation_system = models.CharField(
        choices=get_translation_system_choices(),
        null=True,
        blank=True,
        max_length=20,
    )

    # If this product should grab browser data, which browsers should
    # it grab browser data for. Note, this value should match what
    # we're inferring from the user agent.
    browser_data_browser = models.CharField(
        max_length=100, blank=True, default=u'',
        help_text=u'Grab browser data for browser product')

    browser = models.CharField(
        max_length=30, blank=True, default=u'',
        help_text=u'User agent inferred browser for this product if any')

    objects = ProductManager()

    def collect_browser_data_for(self, browser):
        """Return whether we should collect browser data from this browser"""
        return browser and browser == self.browser_data_browser

    def __unicode__(self):
        return self.display_name

    def __repr__(self):
        return self.__unicode__().encode('ascii', 'ignore')


class ResponseManager(models.Manager):
    def need_translations(self, date_start=None, date_end=None):
        """Returns responses that are translationless

        Allows for optional timeframe so we can use this for
        identifying instances that need to be backfilled.

        """
        objs = self.filter(translated_description='')
        if date_start:
            objs = objs.filter(created__gte=date_start)
        if date_end:
            objs = objs.filter(created__lte=date_end)
        return objs


@register_auto_translation
@register_live_index
class Response(ModelBase):
    """Basic feedback response

    This consists of a bunch of information some of which is inferred
    and some of which comes from the source.

    Some fields are "sacrosanct" and should never be edited after the
    response was created:

    * happy
    * url
    * description
    * user_agent
    * manufacturer
    * device
    * created

    """

    # Data coming from the user
    happy = models.BooleanField(default=True)
    url = EnhancedURLField(blank=True)
    description = models.TextField()

    # Translation into English of the description
    translated_description = models.TextField(blank=True)

    category = models.CharField(max_length=50, blank=True, null=True,
                                default=u'')

    # Data inferred from urls or explicitly stated by the thing saving
    # the data (webform, client of the api, etc)
    product = models.CharField(max_length=30, blank=True)
    platform = models.CharField(max_length=30, blank=True)
    channel = models.CharField(max_length=30, blank=True)
    version = models.CharField(max_length=30, blank=True)
    locale = models.CharField(max_length=8, blank=True)
    country = models.CharField(max_length=4, blank=True, null=True,
                               default=u'')

    manufacturer = models.CharField(max_length=255, blank=True)
    device = models.CharField(max_length=255, blank=True)

    # If using the api, this is the version of the api used. Otherwise
    # null.
    api = models.IntegerField(null=True, blank=True)

    # User agent and inferred data from the user agent
    user_agent = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=30, blank=True)
    browser_version = models.CharField(max_length=30, blank=True)
    browser_platform = models.CharField(max_length=30, blank=True)

    source = models.CharField(max_length=100, blank=True, null=True,
                              default=u'')
    campaign = models.CharField(max_length=100, blank=True, null=True,
                                default=u'')

    created = models.DateTimeField(default=datetime.now)

    objects = ResponseManager()

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u'(%s) %s' % (self.sentiment, self.truncated_description)

    def __repr__(self):
        return self.__unicode__().encode('ascii', 'ignore')

    def generate_translation_jobs(self, system=None):
        """Returns a list of tuples, one for each translation job

        If the locale of this response is English, then we just copy over
        the description and we're done.

        If the product of this response isn't set up for
        auto-translation and no translation system was specified in
        the arguments, then we're done.

        If we already have a response with this text that's
        translated, we copy the most recent translation over.

        Otherwise we generate a list of jobs to be done.

        """
        if self.translated_description:
            return []

        # If the text is coming from an English-speaking locale, we
        # assume it's also in English and just copy it over. We do
        # this regardless of whether auto-translation is enabled or
        # not for this product.
        if self.locale and self.locale.startswith('en'):
            self.translated_description = self.description
            self.save()
            return []

        if not system:
            try:
                prod = Product.objects.get(db_name=self.product)
                system = prod.translation_system
            except Product.DoesNotExist:
                # If the product doesn't exist, then I don't know
                # what's going on. Regardless, we shouldn't create any
                # translation jobs.
                return []

        if not system:
            # If this product isn't set up for translation, don't
            # translate it.
            return []

        try:
            # See if this text has been translated already--if so, use
            # the most recent translation.
            existing_translation = (
                Response.objects
                .filter(description=self.description)
                .filter(locale=self.locale)
                .exclude(translated_description__isnull=True)
                .exclude(translated_description=u'')
                .values_list('translated_description')
                .latest('id')
            )
            self.translated_description = existing_translation[0]
            self.save()
            statsd.incr('feedback.translation.used_existing')
            return []
        except Response.DoesNotExist:
            pass

        return [
            # key, system, src language, src field, dst language, dst field
            (instance_to_key(self), system, self.locale, 'description',
             u'en', 'translated_description')
        ]

    @classmethod
    def get_export_keys(cls, confidential=False):
        """Returns set of keys that are interesting for export

        Some parts of the Response aren't very interesting. This lets
        us explicitly state what is available for export.

        Note: This returns the name of *properties* of Response which
        aren't all database fields. Some of them are finessed.

        :arg confidential: Whether or not to include confidential data

        """
        keys = [
            'id',
            'created',
            'sentiment',
            'description',
            'translated_description',
            'category',
            'product',
            'channel',
            'version',
            'locale_name',
            'manufacturer',
            'device',
            'platform',
            'browser',
            'browser_version',
            'browser_platform',
        ]

        if confidential:
            keys.extend([
                'url',
                'country_name',
                'user_email',
            ])
        return keys

    def save(self, *args, **kwargs):
        self.description = self.description.strip()[:TRUNCATE_LENGTH]
        super(Response, self).save(*args, **kwargs)

    @property
    def url_domain(self):
        """Returns the domain part of a url"""
        return get_domain(self.url)

    @property
    def user_email(self):
        """Associated email address or u''"""
        if self.responseemail_set.count() > 0:
            return self.responseemail_set.all()[0].email
        return u''

    @property
    def has_browserdata(self):
        if self.responsepi_set.exists():
            return True
        return False

    @property
    def sentiment(self):
        if self.happy:
            return _lazy(u'Happy')
        return _lazy(u'Sad')

    @property
    def truncated_description(self):
        """Shorten feedback for list display etc."""
        return smart_truncate(self.description, length=70)

    @property
    def locale_name(self, native=False):
        """Convert a locale code into a human readable locale name"""
        locale = self.locale
        if locale in product_details.languages:
            display_locale = 'native' if native else 'English'
            return product_details.languages[locale][display_locale]

        return locale

    @property
    def country_name(self, native=False):
        """Convert a country code into a human readable country name"""
        country = self.country
        if country in CODE_TO_COUNTRY:
            display_locale = 'native' if native else 'English'
            return CODE_TO_COUNTRY[country][display_locale]

        return country

    @classmethod
    def get_doctype(self):
        return ResponseDocType

    @classmethod
    def infer_product(cls, browser):
        # FIXME: This is hard-coded.
        if browser.browser == u'Firefox for Android':
            return u'Firefox for Android'

        elif browser.platform == u'Firefox OS':
            return u'Firefox OS'

        elif browser.platform in (u'', u'Unknown'):
            return u''

        # FIXME: We can do this because our user agent parser only
        # knows about Mozilla browsers. If we ever change user agent
        # parsers, we'll need to rethink this.
        return u'Firefox'

    @classmethod
    def infer_platform(cls, product, browser):
        # FIXME: This is hard-coded.
        if product == u'Firefox OS':
            return u'Firefox OS'

        elif product == u'Firefox for Android':
            return u'Android'

        elif (browser.browser == u'Firefox' and
              product in (u'Firefox', u'Firefox dev')):
            if browser.platform == 'Windows':
                return browser.platform + ' ' + browser.platform_version
            return browser.platform

        elif product == u'Firefox for iOS':
            return browser.platform + ' ' + browser.platform_version

        return u''


class ResponseDocTypeManager(FjordDocTypeManager):
    @classmethod
    def get_doctype(cls):
        return ResponseDocType

    @classmethod
    def get_indexable(cls):
        return super(ResponseDocTypeManager, cls).get_indexable().reverse()

    @classmethod
    def to_public(cls, docs):
        """Converts this data to dicts with only publicly ok data

        :args docs: list of ResponseDocType instances

        :returns: list of dicts of publicly ok data

        """
        public_fields = cls.get_doctype().public_fields()

        def publicfy(doc):
            doc = doc.to_dict()
            return dict(
                (key, doc.get(key, None))
                for key in public_fields
            )

        return [publicfy(doc) for doc in docs]


@register_doctype
class ResponseDocType(FjordDocType):
    id = es_dsl.Integer()
    happy = es_dsl.Boolean()
    api = es_dsl.Integer()
    url = es_dsl.String(index='not_analyzed')
    url_domain = es_dsl.String(index='not_analyzed')
    has_email = es_dsl.Boolean()
    description = es_dsl.String(analyzer='snowball')
    category = es_dsl.String(index='not_analyzed')
    description_bigrams = es_dsl.String(index='not_analyzed')
    description_terms = es_dsl.String(analyzer='standard')
    user_agent = es_dsl.String(index='not_analyzed')
    product = es_dsl.String(index='not_analyzed')
    channel = es_dsl.String(index='not_analyzed')
    version = es_dsl.String(index='not_analyzed')
    browser = es_dsl.String(index='not_analyzed')
    browser_version = es_dsl.String(index='not_analyzed')
    platform = es_dsl.String(index='not_analyzed')
    locale = es_dsl.String(index='not_analyzed')
    country = es_dsl.String(index='not_analyzed')
    device = es_dsl.String(index='not_analyzed')
    manufacturer = es_dsl.String(index='not_analyzed')
    source = es_dsl.String(index='not_analyzed')
    campaign = es_dsl.String(index='not_analyzed')
    souce_campaign = es_dsl.String(index='not_analyzed')
    organic = es_dsl.Boolean()
    created = es_dsl.Date()

    docs = ResponseDocTypeManager()

    class Meta:
        pass

    def mlt(self):
        """Returns a search with a morelikethis query for docs like this"""
        # Short responses tend to not repeat any words, so then MLT
        # returns nothing. This fixes that by setting min_term_freq to
        # 1. Longer responses tend to repeat important words, so we can
        # set min_term_freq to 2.
        num_words = len(self.description.split(' '))
        if num_words > 40:
            min_term_freq = 2
        else:
            min_term_freq = 1

        s = self.search()
        if self.product:
            s = s.filter('term', product=self.product)
        if self.platform:
            s = s.filter('term', platform=self.platform)

        s = s.query(
            'more_like_this',
            fields=['description'],
            docs=[
                {
                    '_index': get_index_name(),
                    '_type': self._doc_type.name,
                    '_id': self.id
                }
            ],
            min_term_freq=min_term_freq,
            stop_words=list(ANALYSIS_STOPWORDS)
        )
        return s

    @classmethod
    def get_model(cls):
        return Response

    @classmethod
    def public_fields(cls):
        """Fields that can be publicly-visible

        .. Note::

           Do NOT include fields that have PII in them.

        """
        return (
            'id',
            'happy',
            'api',
            'url_domain',
            'has_email',
            'description',
            'category',
            'description_bigrams',
            'user_agent',
            'product',
            'version',
            'platform',
            'locale',
            'source',
            'campaign',
            'organic',
            'created'
        )

    @property
    def truncated_description(self):
        """Shorten feedback for dashboard view."""
        return smart_truncate(self.description, length=500)

    @classmethod
    def extract_doc(cls, resp, with_id=True):
        """Converts a Response to a dict of values

        This can be used with ``ResponseDocType.from_obj()`` to create a
        ``ResponseDocType`` object or it can be used for indexing.

        :arg resp: a Response object
        :arg with_id: whether or not to include the ``_id`` value--include
            it when you're bulk indexing

        :returns: a dict

        """
        doc = {
            'id': resp.id,
            'happy': resp.happy,
            'api': resp.api,
            'url': resp.url,
            'url_domain': resp.url_domain,
            'has_email': bool(resp.user_email),
            'description': resp.description,
            'user_agent': resp.user_agent,
            'product': resp.product,
            'channel': resp.channel,
            'version': resp.version,
            'browser': resp.browser,
            'browser_version': resp.browser_version,
            'platform': resp.platform,
            'locale': resp.locale,
            'country': resp.country,
            'device': resp.device,
            'manufacturer': resp.manufacturer,
            'source': resp.source,
            'campaign': resp.campaign,
            'source_campaign': '::'.join([
                (resp.source or '--'),
                (resp.campaign or '--')
            ]),
            'organic': (not resp.campaign),
            'created': resp.created
        }

        # We only compute bigrams for english because the analysis
        # uses English stopwords, stemmers, ...
        if resp.locale.startswith(u'en') and resp.description:
            doc['description_bigrams'] = compute_grams(resp.description)
        else:
            doc['description_bigrams'] = []

        if with_id:
            doc['_id'] = doc['id']
        return doc


class ResponseEmail(ModelBase):
    """Holds email addresses related to Responses."""

    opinion = models.ForeignKey(Response)
    email = models.EmailField()

    def __unicode__(self):
        return unicode(self.id)


class ResponseContext(ModelBase):
    """Holds context data we were sent as a JSON blob."""

    opinion = models.ForeignKey(Response)
    data = JSONObjectField()

    def __unicode__(self):
        return unicode(self.id)


class ResponsePI(ModelBase):
    """Holds remote-troubleshooting and other product data."""
    opinion = models.ForeignKey(Response)
    data = JSONObjectField()

    def __unicode__(self):
        return unicode(self.id)


class PostResponseSerializer(serializers.Serializer):
    """This handles incoming feedback

    This handles responses as well as the additional data for response
    emails and slop.

    """
    # We want to require the happy field, but we can't because for a
    # long while we used a version of DRF which had a bug where a
    # BooleanField marked as required would actually just default to
    # False if a value wasn't provided. Bug #1155600 means we need to
    # maintain that old (busted) behavior. Thus we need to not require
    # this and instead default it to False.
    happy = serializers.BooleanField(default=False)

    url = serializers.CharField(max_length=200, allow_blank=True, default=u'')
    description = serializers.CharField(required=True)

    category = serializers.CharField(
        max_length=50, allow_blank=True, default=u'')

    # product, channel, version, locale, platform
    product = serializers.CharField(
        max_length=20, required=True, allow_null=False)
    channel = serializers.CharField(
        max_length=30, allow_blank=True, default=u'')
    version = serializers.CharField(
        max_length=30, allow_blank=True, default=u'')
    locale = serializers.CharField(
        max_length=8, allow_blank=True, default=u'')
    platform = serializers.CharField(
        max_length=30, allow_blank=True, default=u'')
    country = serializers.CharField(
        max_length=4, allow_blank=True, default=u'')

    # device information
    manufacturer = serializers.CharField(
        max_length=255, allow_blank=True, default=u'')
    device = serializers.CharField(
        max_length=255, allow_blank=True, default=u'')

    # user's email address
    email = serializers.EmailField(required=False)

    # user agent
    user_agent = serializers.CharField(
        max_length=255, allow_blank=True, default=u'')

    # source and campaign
    source = serializers.CharField(
        max_length=100, allow_blank=True, default=u'')
    campaign = serializers.CharField(
        max_length=100, allow_blank=True, default=u'')

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                u'This field may not be blank.'
            )
        return value

    def validate_url(self, value):
        if value:
            if not is_url(value):
                raise serializers.ValidationError(
                    u'{0} is not a valid url'.format(value)
                )
        return value

    def validate_product(self, value):
        """Validates the product against Product model"""
        # This looks goofy, but it makes it more likely we have a
        # cache hit.
        products = Product.objects.values_list('display_name', flat=True)
        if value not in products:
            raise serializers.ValidationError(
                u'{0} is not a valid product'.format(value)
            )
        return value

    def create(self, validated_data):
        # First, pop out 'email' since it's not in the Response.
        validated_data.pop('email', None)

        # Strip string data
        for key in ['url', 'description', 'category', 'product',
                    'channel', 'version', 'platform', 'locale',
                    'manufacturer', 'device', 'country', 'source',
                    'campaign', 'user_agent']:
            if key in validated_data:
                validated_data[key] = validated_data[key].strip()

        # If there's a user agent, infer all the things from
        # the user agent.
        user_agent = validated_data.get('user_agent')
        if user_agent:
            browser = parse_ua(user_agent)
            validated_data['browser'] = browser.browser
            validated_data['browser_version'] = browser.browser_version
            bp = browser.platform
            if browser.platform == 'Windows':
                bp += (' ' + browser.platform_version)
            validated_data['browser_platform'] = bp

        return Response.objects.create(api=1, **validated_data)

    def save(self):
        obj = super(PostResponseSerializer, self).save()

        if 'email' in self.initial_data:
            ResponseEmail.objects.create(
                email=self.initial_data['email'].strip(),
                opinion=obj
            )

        slop = {}
        data_items = sorted(self.initial_data.items())
        for key, val in data_items:
            if key in self.validated_data:
                continue
            # Restrict key to 20 characters
            key = key[:20]

            # Restrict value to 100 characters
            val = val[:100]
            slop[key] = val

            # Only collect 20 pairs max
            if len(slop) >= 20:
                break

        if slop:
            ResponseContext.objects.create(data=slop, opinion=obj)

        return obj


@register_purger
def purge_data():
    """Purges feedback data

    * ResponseEmail >= 180 days
    * ResponseContext >= 180 days
    * ResponsePI >= 180 days

    """
    cutoff = datetime.now() - timedelta(days=180)

    responses_to_update = set()

    # First, ResponseEmail.
    objs = ResponseEmail.objects.filter(opinion__created__lte=cutoff)
    responses_to_update.update(objs.values_list('opinion_id', flat=True))
    count = objs.count()
    objs.delete()
    msg = 'feedback_responseemail: %d, ' % (count, )

    # Second, ResponseContext.
    objs = ResponseContext.objects.filter(opinion__created__lte=cutoff)
    responses_to_update.update(objs.values_list('opinion_id', flat=True))
    count = objs.count()
    objs.delete()
    msg += 'feedback_responsecontext: %d, ' % (count, )

    # Third, ResponsePI.
    objs = ResponsePI.objects.filter(
        opinion__created__lte=cutoff)
    responses_to_update.update(objs.values_list('opinion_id', flat=True))
    count = objs.count()
    objs.delete()
    msg += 'feedback_responsepi: %d' % (count, )

    if responses_to_update:
        index_chunk(ResponseDocType, list(responses_to_update))

    return msg
