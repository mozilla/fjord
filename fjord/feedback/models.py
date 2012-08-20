from django.db import models
from tower import ugettext_lazy as _


from fjord.base.models import ModelBase
from fjord.base.util import smart_truncate


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

    created = models.DateTimeField(auto_now_add=True)

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

    # TODO: Implement this when we implement view
    #
    # @models.permalink
    # def get_absolute_url(self):
    #     return ('xxx', [str(self.id)])


