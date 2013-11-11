from datetime import datetime

from django.conf import settings
from django.db import models

from elasticutils.contrib.django import Indexable
from rest_framework import serializers
from tower import ugettext_lazy as _

from fjord.base.models import ModelBase
from fjord.base.util import smart_truncate
from fjord.feedback import config
from fjord.search.index import (
    register_mapping_type, FjordMappingType,
    boolean_type, date_type, integer_type, keyword_type, text_type)
from fjord.search.tasks import register_live_index


# This defines the number of characters the description can have.  We
# do this in code rather than in the db since it makes it easier to
# tweak the value.
TRUNCATE_LENGTH = 10000


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

    # This is the product/channel.
    # e.g. "firefox.desktop.stable", "firefox.mobile.aurora", etc.
    prodchan = models.CharField(max_length=255)

    # Data coming from the user
    happy = models.BooleanField(default=True)
    url = models.URLField(verify_exists=False, blank=True)
    description = models.TextField(blank=True)

    # Translation into English of the description
    translated_description = models.TextField(blank=True)

    # Data inferred from urls or explicitly stated by the thing saving
    # the data (webform, client of the api, etc)
    product = models.CharField(max_length=30, blank=True)
    channel = models.CharField(max_length=30, blank=True)
    version = models.CharField(max_length=30, blank=True)
    locale = models.CharField(max_length=8, blank=True)
    country = models.CharField(max_length=4, blank=True, null=True,
                               default=u'')

    manufacturer = models.CharField(max_length=255, blank=True)
    device = models.CharField(max_length=255, blank=True)

    # User agent and inferred data from the user agent
    user_agent = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=30, blank=True)
    browser_version = models.CharField(max_length=30, blank=True)
    platform = models.CharField(max_length=30, blank=True)

    created = models.DateTimeField(default=datetime.now)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u'(%s) %s' % (self.sentiment, self.truncated_description)

    def __repr__(self):
        return self.__unicode__().encode('ascii', 'ignore')

    def save(self, *args, **kwargs):
        self.description = self.description.strip()[:TRUNCATE_LENGTH]
        super(Response, self).save(*args, **kwargs)

    @property
    def sentiment(self):
        if self.happy:
            return _(u'Happy')
        return _(u'Sad')

    @property
    def truncated_description(self):
        """Shorten feedback for list display etc."""
        return smart_truncate(self.description, length=70)

    @classmethod
    def get_mapping_type(self):
        return ResponseMappingType

    @classmethod
    def infer_product(cls, platform):
        if platform == u'Firefox OS':
            return u'Firefox OS'

        elif platform == u'Android':
            return u'Firefox for Android'

        elif platform in (u'', u'Unknown'):
            return u''

        return u'Firefox'


@register_mapping_type
class ResponseMappingType(FjordMappingType, Indexable):
    @classmethod
    def get_model(cls):
        return Response

    @classmethod
    def get_mapping(cls):
        return {
            'id': integer_type(),
            'prodchan': keyword_type(),
            'happy': boolean_type(),
            'url': keyword_type(),
            'description': text_type(),
            'user_agent': keyword_type(),
            'product': keyword_type(),
            'channel': keyword_type(),
            'version': keyword_type(),
            'browser': keyword_type(),
            'browser_version': keyword_type(),
            'platform': keyword_type(),
            'locale': keyword_type(),
            'device': keyword_type(),
            'manufacturer': keyword_type(),
            'created': date_type()
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

        def empty_to_unknown(text):
            return u'Unknown' if text == u'' else text

        return {
            'id': obj.id,
            'prodchan': obj.prodchan,
            'happy': obj.happy,
            'url': obj.url,
            'description': obj.description,
            'user_agent': obj.user_agent,
            'product': obj.product,
            'channel': obj.channel,
            'version': obj.version,
            'browser': obj.browser,
            'browser_version': obj.browser_version,
            'platform': obj.platform,
            'locale': obj.locale,
            'device': obj.device,
            'manufacturer': obj.manufacturer,
            'created': obj.created,
        }


class ResponseEmail(ModelBase):
    """Holds email addresses related to Responses."""

    opinion = models.ForeignKey(Response)
    email = models.EmailField()


class ResponseSerializer(serializers.Serializer):
    """This handles incoming feedback

    This handles responses as well as the additional data for response
    emails.

    """
    happy = serializers.BooleanField(required=True)
    url = serializers.URLField(required=False, default=u'')
    description = serializers.CharField(required=True)

    # Note: API clients don't provide a user_agent, so we skip that and
    # browser since those don't make sense.

    # product, channel, version, locale, platform
    product = serializers.ChoiceField(choices=config.PRODUCTS, required=True)
    channel = serializers.CharField(max_length=30, required=False, default=u'')
    version = serializers.CharField(max_length=30, required=False, default=u'')
    locale = serializers.CharField(max_length=8, required=False, default=u'')
    platform = serializers.CharField(max_length=30, required=False, default=u'')
    country = serializers.CharField(max_length=4, required=False, default=u'')

    # device information
    manufacturer = serializers.CharField(required=False, default=u'')
    device = serializers.CharField(required=False, default=u'')

    # user's email address
    email = serializers.EmailField(required=False)

    def restore_object(self, attrs, instance=None):
        # Note: instance should never be anything except None here
        # since we only accept POST and not PUT/PATCH.

        # prodchan is composed of product + channel. This is a little
        # goofy, but we can fix it later if we bump into issues with
        # the contents.
        prodchan = u'.'.join([
            attrs['product'].lower().replace(' ', '') or 'unknown',
            attrs['channel'].lower().replace(' ', '') or 'unknown'])

        opinion = Response(
            prodchan=prodchan,
            happy=attrs['happy'],
            url=attrs['url'].strip(),
            description=attrs['description'].strip(),
            user_agent=u'api',  # Hard-coded
            product=attrs['product'].strip(),
            channel=attrs['channel'].strip(),
            version=attrs['version'].strip(),
            platform=attrs['platform'].strip(),
            locale=attrs['locale'].strip(),
            manufacturer=attrs['manufacturer'].strip(),
            device=attrs['device'].strip(),
            country=attrs['country'].strip()
        )

        # If there is an email address, stash it on this instance so
        # we can save it later in .save() and so it gets returned
        # correctly in the response. This doesn't otherwise affect the
        # Response model instance.
        opinion.email = attrs.get('email', '').strip()

        return opinion

    def save_object(self, obj, **kwargs):
        obj.save(**kwargs)

        if obj.email:
            opinion_email = ResponseEmail(
                email=obj.email,
                opinion=obj
            )
            opinion_email.save(**kwargs)

        return obj
