from django.db import models

from fjord.base.models import ModelBase
from fjord.feedback.models import Response


class Flag(ModelBase):
    """Flags on responses"""
    name = models.CharField(max_length=20)
    responses = models.ManyToManyField(Response)

    def __str__(self):
        return self.name


class Store(ModelBase):
    # the module/class of the thing this entry belongs to
    classifier = models.CharField(max_length=50)

    # a token like "browser"; this is a text field because tokens
    # can be arbitrarily long
    key = models.TextField()

    # JSON blob
    value = models.TextField()

    def __str__(self):
        return '%s:%s' % (self.classifier, self.key)
