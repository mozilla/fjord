from django.db import models

from fjord.base.models import ModelBase
from fjord.feedback.models import Response


class Flag(ModelBase):
    """Flags on responses"""
    name = models.CharField(max_length=20)
    responses = models.ManyToManyField(Response)

    def __str__(self):
        return self.name
