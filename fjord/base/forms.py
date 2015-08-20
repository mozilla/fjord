from django.forms import fields
from django.forms import widgets

from fjord.base.validators import EnhancedURLValidator


class StringListField(fields.CharField):
    widget = widgets.Textarea()

    def prepare_value(self, value):
        """Converts a value into a value appropriate for a Textarea widget

        :arg value: None or a list of unicode strings

        :returns: unicode string

        """
        if not value:
            value = u''
        else:
            value = u'\n'.join(value)
        return value

    def clean(self, value):
        """Converts a value from the HTML form to a ListField value

        This also strips each individual unicode to remove space
        before and after the value.

        :arg value: unicode string

        :returns: list of unicodes

        """
        values = super(StringListField, self).clean(value)
        val = [val.strip() for val in values.splitlines() if val]
        return val


class EnhancedURLField(fields.URLField):
    """URLField that also supports about: and chrome:// urls"""
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(EnhancedURLField, self).__init__(
            max_length, min_length, *args, **kwargs)
        # The last validator in the list is the URLValidator we don't
        # like. Replace that one with ours.
        self.validators[-1] = EnhancedURLValidator()

    def to_python(self, value):
        if value:
            # Don't "clean" about: and chrome:// urls--just pass them
            # through.
            if value.startswith(('about:', 'chrome://')):
                return value

        return super(EnhancedURLField, self).to_python(value)
