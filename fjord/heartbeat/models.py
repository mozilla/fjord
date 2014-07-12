from django.db import models

from fjord.base.models import ModelBase, JSONObjectField


class Poll(ModelBase):
    """Defines a Heartbeat poll"""
    slug = models.SlugField(unique=True)
    description= models.TextField(default=u'', blank=True)
    status = models.CharField(max_length=1000, blank=True, default=u'')
    enabled = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s: %s' % (self.slug,
                           'enabled' if self.enabled else 'disabled')


class Answer(ModelBase):
    """Defines a Heartbeat poll answer"""
    locale = models.CharField(max_length=8)
    platform = models.CharField(max_length=30)
    product = models.CharField(max_length=30)
    version = models.CharField(max_length=30)
    channel = models.CharField(max_length=30)

    # This is used as a dumping ground for arbitrary contextual data.
    extra = JSONObjectField(default=u'{}')

    poll = models.ForeignKey(Poll, to_field='slug')
    answer = models.CharField(max_length=10)

    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s: %s - %s' % (self.id, self.poll.slug, self.answer)
