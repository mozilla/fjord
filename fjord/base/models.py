from django.contrib.auth.models import User
from django.db import models

import caching.base


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all models: Implements caching."""

    objects = caching.base.CachingManager()
    uncached = models.Manager()

    class Meta:
        abstract = True


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    def display_name(self):
        return self.user.first_name or self.user.email
