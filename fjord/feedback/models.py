from datetime import datetime

from django.db import models

from elasticutils.contrib.django import Indexable
from tower import ugettext_lazy as _

from fjord.base.models import ModelBase
from fjord.base.util import smart_truncate
from fjord.search.index import (
    register_mapping_type, FjordMappingType,
    boolean_type, date_type, integer_type, keyword_type, text_type)
from fjord.search.tasks import register_live_index


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
        if platform == u'FirefoxOS':
            return u'Firefox OS'

        elif platform == u'Android':
            return u'Firefox for Android'

        elif platform == u'Unknown':
            return u'Unknown'

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
