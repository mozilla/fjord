import json

from django.contrib.auth.models import User
from django.db import models

import caching.base
from tower import ugettext_lazy as _lazy


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all models: Implements caching."""

    objects = caching.base.CachingManager()
    uncached = models.Manager()

    class Meta:
        abstract = True


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class JSONObjectField(models.TextField):
    """Represents a JSON object.

    Note: This might be missing a lot of Django infrastructure to
    work correctly across edge cases. Also it was tested with MySQL
    and no other db backends.

    """
    empty_strings_allowed = False
    description = _lazy(u'JSON Object')

    def to_python(self, value):
        return json.loads(value)

    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        return json.dumps(val, sort_keys=True) if val else '{}'


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^fjord\.base\.models\.JSONObjectField"])
