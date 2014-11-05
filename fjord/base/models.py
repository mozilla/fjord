import json

from django.contrib.auth.models import User
from django.db import models

import caching.base
from tower import ugettext_lazy as _lazy

from fjord.base import forms
from fjord.base.validators import EnhancedURLValidator


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all models: Implements caching."""

    objects = caching.base.CachingManager()
    uncached = models.Manager()

    class Meta:
        abstract = True


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class EnhancedURLField(models.CharField):
    """URLField that also supports about: and chrome:// urls"""
    description = 'Enhanced URL'

    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        models.CharField.__init__(self, verbose_name, name, **kwargs)
        self.validators.append(EnhancedURLValidator())

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.EnhancedURLField,
        }
        defaults.update(kwargs)
        return super(EnhancedURLField, self).formfield(**defaults)


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^fjord\.base\.models\.EnhancedURLField"])


class JSONObjectField(models.TextField):
    """Represents a JSON object.

    Note: This might be missing a lot of Django infrastructure to
    work correctly across edge cases. Also it was tested with MySQL
    and no other db backends.

    """
    empty_strings_allowed = False
    description = _lazy(u'JSON Object')

    def __init__(self, *args, **kwargs):
        # "default" should default to an empty JSON dict. We implement
        # that this way rather than getting involved in the
        # get_default/has_default Field machinery since this makes it
        # easier to subclass.
        kwargs['default'] = kwargs.get('default', u'{}')
        super(JSONObjectField, self).__init__(self, *args, **kwargs)

    def pre_init(self, value, obj):
        if obj._state.adding:
            if isinstance(value, basestring):
                return json.loads(value)
        return value

    def to_python(self, value):
        # FIXME: This isn't called when accessing the field value.
        # So it must be something else.
        return json.loads(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if self.null and value is None:
            return None
        return json.dumps(value, sort_keys=True) if value else '{}'

    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        return self.get_db_prep_value(val)


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^fjord\.base\.models\.JSONObjectField"])
