import ast
import json

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _lazy

from fjord.base import forms
from fjord.base.validators import EnhancedURLValidator


# Common base model for all fjord models
ModelBase = models.Model


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class ListField(models.TextField):
    description = _lazy('List of values')

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """Converts the value to a Python value

        :arg value: None, list or unicode from the db

        :returns: list of things

        """
        if not value:
            value = []

        if isinstance(value, list):
            return value

        try:
            # This takes a unicode and reconsistutes it into Python base
            # types.
            value = ast.literal_eval(value)
            assert isinstance(value, list)
            return value
        except Exception as exc:
            # Need to return a ValidationError, but this throws a
            # SyntaxError, so we (poorly) wrap it.
            raise ValidationError(repr(exc))

    def get_prep_value(self, value):
        """Perform preliminary non-db specific value checks and conversions"""
        if value is None:
            return value

        return unicode(value)

    def value_to_string(self, obj):
        """Returns a string value of this field from the passed obj

        Used by the serialization framework.

        """
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


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

    def deconstruct(self):
        name, path, args, kwargs = super(EnhancedURLField, self).deconstruct()

        # Don't serialize the default value which allows us to change
        # default values later without the serialized form changing.
        if kwargs.get('max_length', None) == 200:
            del kwargs['max_length']

        return name, path, args, kwargs


class JSONObjectField(models.Field):
    """Represents a JSON object.

    Note: This might be missing a lot of Django infrastructure to
    work correctly across edge cases. Also it was tested with MySQL
    and no other db backends.

    """
    empty_strings_allowed = False
    description = _lazy(u'JSON Object')

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        # "default" should default to an empty JSON dict. We implement
        # that this way rather than getting involved in the
        # get_default/has_default Field machinery since this makes it
        # easier to subclass.
        kwargs['default'] = kwargs.get('default', {})
        super(JSONObjectField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'TextField'

    def pre_init(self, value, obj):
        if obj._state.adding:
            if isinstance(value, basestring):
                return json.loads(value)
        return value

    def to_python(self, value):
        if isinstance(value, basestring):
            return json.loads(value)
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        if self.null and value is None:
            return None
        return json.dumps(value, sort_keys=True)

    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        return self.get_db_prep_value(val, None)

    def value_from_object(self, obj):
        value = super(JSONObjectField, self).value_from_object(obj)
        if self.null and value is None:
            return None
        return json.dumps(value)

    def get_default(self):
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default

        if self.null:
            return None
        return {}

    def deconstruct(self):
        name, path, args, kwargs = super(JSONObjectField, self).deconstruct()

        # Don't serialize the default value which allows us to change
        # default values later without the serialized form changing.
        if kwargs.get('default', None) == {}:
            del kwargs['default']

        return name, path, args, kwargs
