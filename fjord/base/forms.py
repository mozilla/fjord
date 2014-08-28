from django.forms import fields

from fjord.base.validators import EnhancedURLValidator


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
