from datetime import datetime

from django.db import models

from elasticutils.contrib.django.models import Indexable
from tower import ugettext_lazy as _

from fjord.base.models import ModelBase
from fjord.base.util import smart_truncate
from fjord.search.index import register_mapping_type, FjordMappingType
from fjord.search.tasks import register_live_index


@register_live_index
class Simple(ModelBase):
    """Feedback item from Firefox Desktop stable form"""

    # This is the product/channel.
    # e.g. "firefox.desktop.stable", "firefox.mobile.aurora", etc.
    prodchan = models.CharField(max_length=255)

    # Data coming from the user
    happy = models.BooleanField(default=True)
    url = models.URLField(verify_exists=False, blank=True)
    description = models.TextField(blank=True)

    # Inferred data
    user_agent = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=30, blank=True)
    browser_version = models.CharField(max_length=30, blank=True)
    platform = models.CharField(max_length=30, blank=True)
    locale = models.CharField(max_length=8, blank=True)

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
        return SimpleIndex

    # TODO: Implement this when we implement view
    #
    # @models.permalink
    # def get_absolute_url(self):
    #     return ('xxx', [str(self.id)])


@register_mapping_type
class SimpleIndex(FjordMappingType, Indexable):
    @classmethod
    def get_model(cls):
        return Simple

    @classmethod
    def get_mapping(cls):
        return {
            'id': {'type': 'integer'},
            'prodchan': {'type': 'string', 'index': 'not_analyzed'},
            'happy': {'type': 'boolean'},
            'url': {'type': 'string', 'index': 'not_analyzed'},
            'description': {'type': 'string', 'analyzer': 'snowball'},
            'user_agent': {'type': 'string', 'index': 'not_analyzed'},
            'browser': {'type': 'string', 'analyzer': 'keyword'},
            'browser_version': {'type': 'string', 'index': 'not_analyzed'},
            'platform': {'type': 'string', 'analyzer': 'keyword'},
            'locale': {'type': 'string', 'analyzer': 'keyword'},
            'created': {'type': 'date'}
            }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

        # Cheating here because at the moment, everything is
        # straight-forward. When that ceases to be the case,
        # we should stop cheating.
        mapping = cls.get_mapping()
        return dict((field, getattr(obj, field))
                    for field in mapping.keys())


class SimpleEmail(ModelBase):
    opinion = models.ForeignKey(Simple)
    email = models.EmailField()
