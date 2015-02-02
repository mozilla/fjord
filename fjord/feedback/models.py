from datetime import datetime, timedelta

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models

from elasticutils.contrib.django import Indexable, MLT
from product_details import product_details
from rest_framework import serializers
from statsd import statsd
from tower import ugettext_lazy as _lazy

from fjord.base.browsers import parse_ua
from fjord.base.domain import get_domain
from fjord.base.models import ModelBase, JSONObjectField, EnhancedURLField
from fjord.base.utils import smart_truncate, instance_to_key, is_url
from fjord.feedback.config import (
    CODE_TO_COUNTRY,
    ANALYSIS_STOPWORDS,
    TRUNCATE_LENGTH
)
from fjord.feedback.utils import compute_grams
from fjord.journal.utils import j_info
from fjord.search.index import (
    register_mapping_type,
    FjordMappingType,
    boolean_type,
    date_type,
    integer_type,
    keyword_type,
    terms_type,
    text_type,
    index_chunk
)
from fjord.search.tasks import register_live_index
from fjord.translations.models import get_translation_system_choices
from fjord.translations.tasks import register_auto_translation


class ProductManager(models.Manager):
    def public(self):
        """Returns publicly visible products"""
        return self.filter(on_dashboard=True)


class Product(ModelBase):
    """Represents a product we capture feedback for"""
    # Whether or not this product is enabled
    enabled = models.BooleanField(default=True)

    # Used internally for notes to make it easier to manage products
    notes = models.CharField(max_length=255, blank=True, default=u'')

    # This is the name we display everywhere
    display_name = models.CharField(max_length=50)

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

    objects = ProductManager()

    @classmethod
    def from_slug(cls, slug):
        return cls.objects.get(slug=slug)

    @classmethod
    def get_product_map(cls):
        """Return map of product slug -> db_name for enabled products"""
        products = (cls.objects
                    .filter(enabled=True)
                    .values_list('slug', 'db_name'))
        return dict(prod for prod in products)

    def collect_browser_data_for(self, browser):
        """Return whether we should collect browser data from this browser"""
        return browser and browser == self.browser_data_browser
        
    def __unicode__(self):
        return self.display_name

    def __repr__(self):
        return self.__unicode__().encode('ascii', 'ignore')


@register_auto_translation
@register_live_index
class Response(ModelBase):
    """Basic feedback response

    This consists of a bunch of information some of which is inferred
    and some of which comes from the source.

    Some fields are "sacrosanct" and should never be edited after the
    response was created:

    * happy
    * rating
    * url
    * description
    * user_agent
    * manufacturer
    * device
    * created

    """

    # Data coming from the user
    happy = models.BooleanField(default=True)
    rating = models.PositiveIntegerField(null=True)
    url = EnhancedURLField(blank=True)
    description = models.TextField(blank=True)

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
        if self.rating is not None:
            self.happy = False if self.rating <= 3 else True
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
    def get_mapping_type(self):
        return ResponseMappingType

    @classmethod
    def infer_product(cls, browser):
        platform = browser.platform

        # FIXME: This is hard-coded.
        if platform == u'Firefox OS':
            return u'Firefox OS'

        elif platform == u'Android':
            return u'Firefox for Android'

        elif platform in (u'', u'Unknown'):
            return u''

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

        return u''


@register_mapping_type
class ResponseMappingType(FjordMappingType, Indexable):
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

    @classmethod
    def reshape(cls, results):
        """Reshapes the results so lists are lists and everything is not"""
        def delist(item):
            return val if key == 'description_bigrams' else val[0]

        return [
            dict([(key, delist(val)) for key, val in result.items()])
            for result in results
        ]

    @classmethod
    def get_mapping(cls):
        return {
            'id': integer_type(),
            'happy': boolean_type(),
            'api': integer_type(),
            'url': keyword_type(),
            'url_domain': keyword_type(),
            'has_email': boolean_type(),
            'description': text_type(),
            'category': text_type(),
            'description_bigrams': keyword_type(),
            'description_terms': terms_type(),
            'user_agent': keyword_type(),
            'product': keyword_type(),
            'channel': keyword_type(),
            'version': keyword_type(),
            'browser': keyword_type(),
            'browser_version': keyword_type(),
            'platform': keyword_type(),
            'locale': keyword_type(),
            'country': keyword_type(),
            'device': keyword_type(),
            'manufacturer': keyword_type(),
            'source': keyword_type(),
            'campaign': keyword_type(),
            'source_campaign': keyword_type(),
            'organic': boolean_type(),
            'created': date_type(),
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

        doc = {
            'id': obj.id,
            'happy': obj.happy,
            'api': obj.api,
            'url': obj.url,
            'url_domain': obj.url_domain,
            'has_email': bool(obj.user_email),
            'description': obj.description,
            'category': obj.category,
            'description_terms': obj.description,
            'user_agent': obj.user_agent,
            'product': obj.product,
            'channel': obj.channel,
            'version': obj.version,
            'browser': obj.browser,
            'browser_version': obj.browser_version,
            'platform': obj.platform,
            'locale': obj.locale,
            'country': obj.country,
            'device': obj.device,
            'manufacturer': obj.manufacturer,
            'source': obj.source,
            'campaign': obj.campaign,
            'source_campaign': '::'.join([
                (obj.source or '--'),
                (obj.campaign or '--')
            ]),
            'organic': (not obj.campaign),
            'created': obj.created,
        }

        # We only compute bigrams for english because the analysis
        # uses English stopwords, stemmers, ...
        if obj.locale.startswith(u'en') and obj.description:
            bigrams = compute_grams(obj.description)
            doc['description_bigrams'] = bigrams

        return doc

    @property
    def truncated_description(self):
        """Shorten feedback for dashboard view."""
        return smart_truncate(self.description, length=500)

    @classmethod
    def get_products(cls):
        """Returns a list of all products

        This is cached.

        """
        key = 'feedback:response_products1'
        products = cache.get(key)
        if products is not None:
            return products

        facet = cls.search().facet('product').facet_counts()
        products = [prod['term'] for prod in facet['product']]

        cache.add(key, products)
        return products

    @classmethod
    def get_indexable(cls):
        return super(ResponseMappingType, cls).get_indexable().reverse()

    @classmethod
    def morelikethis(cls, resp):
        """Returns a list of responses that are like the specified one"""
        s = cls.search()
        s = s.filter(happy=resp.happy)
        if resp.product:
            s = s.filter(product=resp.product)
        if resp.platform:
            s = s.filter(platform=resp.platform)

        # Short responses tend to not repeat any words, so then MLT
        # returns nothing. This fixes that by setting min_term_freq to
        # 1. Longer responses tend to repeat important words, so we can
        # set min_term_freq to 2.
        num_words = len(resp.description.split(' '))
        if num_words > 40:
            min_term_freq = 2
        else:
            min_term_freq = 1

        return MLT(
            id_=resp.id,
            s=s,
            mlt_fields=['description'],
            index=cls.get_index(),
            doctype=cls.get_mapping_type_name(),
            stop_words=list(ANALYSIS_STOPWORDS),
            min_term_freq=min_term_freq
        )


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


class NoNullsCharField(serializers.CharField):
    """Further restricts CharField so it doesn't accept nulls

    DRF lets CharFields take nulls which is not what I want. This
    raises a ValidationError if the value is a null.

    """
    def from_native(self, value):
        if value is None:
            raise ValidationError('Value cannot be null')
        return super(NoNullsCharField, self).from_native(value)


class PostResponseSerializer(serializers.Serializer):
    """This handles incoming feedback

    This handles responses as well as the additional data for response
    emails.

    """
    happy = serializers.BooleanField(required=True)
    url = serializers.CharField(max_length=200, required=False, default=u'')
    description = serializers.CharField(required=True)

    category = serializers.CharField(max_length=50, required=False,
                                     default=u'')

    # product, channel, version, locale, platform
    product = NoNullsCharField(max_length=20, required=True)
    channel = NoNullsCharField(max_length=30, required=False, default=u'')
    version = NoNullsCharField(max_length=30, required=False, default=u'')
    locale = NoNullsCharField(max_length=8, required=False, default=u'')
    platform = NoNullsCharField(max_length=30, required=False, default=u'')
    country = NoNullsCharField(max_length=4, required=False, default=u'')

    # device information
    manufacturer = NoNullsCharField(max_length=255, required=False,
                                    default=u'')
    device = NoNullsCharField(max_length=255, required=False, default=u'')

    # user's email address
    email = serializers.EmailField(required=False)

    # user agent
    user_agent = NoNullsCharField(max_length=255, required=False, default=u'')

    # source and campaign
    source = NoNullsCharField(max_length=100, required=False, default=u'')
    campaign = NoNullsCharField(max_length=100, required=False, default=u'')

    def validate_url(self, attrs, source):
        value = attrs[source]
        if value:
            if not is_url(value):
                raise serializers.ValidationError(
                    '{0} is not a valid url'.format(value))

        return attrs

    def validate_product(self, attrs, source):
        """Validates the product against Product model"""
        value = attrs[source]

        # This looks goofy, but it makes it more likely we have a
        # cache hit.
        products = Product.objects.values_list('display_name', flat=True)
        if value not in products:
            raise serializers.ValidationError(
                '{0} is not a valid product'.format(value))
        return attrs

    def restore_object(self, attrs, instance=None):
        # Note: instance should never be anything except None here
        # since we only accept POST and not PUT/PATCH.

        opinion = Response(
            happy=attrs['happy'],
            url=attrs['url'].strip(),
            description=attrs['description'].strip(),
            category=attrs['category'].strip(),
            product=attrs['product'].strip(),
            channel=attrs['channel'].strip(),
            version=attrs['version'].strip(),
            platform=attrs['platform'].strip(),
            locale=attrs['locale'].strip(),
            manufacturer=attrs['manufacturer'].strip(),
            device=attrs['device'].strip(),
            country=attrs['country'].strip(),
            source=attrs['source'].strip(),
            campaign=attrs['campaign'].strip(),
            api=1,  # Hard-coded api version number
        )

        # If there's a user agent, infer all the things from the user
        # agent.
        user_agent = attrs['user_agent'].strip()
        if user_agent:
            opinion.user_agent = user_agent
            browser = parse_ua(user_agent)
            opinion.browser = browser.browser
            opinion.browser_version = browser.browser_version
            opinion.browser_platform = browser.platform
            if browser.platform == 'Windows':
                opinion.browser_platform += (' ' + browser.platform_version)

        # If there is an email address, stash it on this instance so
        # we can save it later in .save() and so it gets returned
        # correctly in the response. This doesn't otherwise affect the
        # Response model instance.
        opinion.email = attrs.get('email', '').strip()

        slop = {}
        data_items = sorted(self.context['request'].DATA.items())
        for key, val in data_items:
            if key in attrs:
                continue
            # Restrict key to 20 characters
            key = key[:20]

            # Restrict value to 100 characters
            val = val[:100]
            slop[key] = val

            # Only collect 20 pairs max
            if len(slop) >= 20:
                break

        opinion.slop = slop

        return opinion

    def save_object(self, obj, **kwargs):
        obj.save(**kwargs)

        if obj.email:
            opinion_email = ResponseEmail(
                email=obj.email,
                opinion=obj
            )
            opinion_email.save(**kwargs)

        if obj.slop:
            context = ResponseContext(
                data=obj.slop,
                opinion=obj
            )
            context.save(**kwargs)

        return obj


def purge_data(cutoff=None, verbose=False):
    """Implements data purging per our data retention policy"""
    responses_to_update = set()

    if cutoff is None:
        # Default to wiping out 180 days ago which is roughly 6 months.
        cutoff = datetime.now() - timedelta(days=180)

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

    j_info(app='feedback',
           src='purge_data',
           action='purge_data',
           msg=msg)

    if responses_to_update:
        index_chunk(ResponseMappingType, list(responses_to_update))
