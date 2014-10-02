from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from fjord.base.utils import is_url


class EnhancedURLValidator(URLValidator):
    """URLValidator that also validates about: and chrome:// urls"""
    def __call__(self, value):
        # is_url turns around and uses URLValidator regex, so this
        # covers everything URLValidator covers plus some other
        # things.
        if not is_url(value):
            raise ValidationError(self.message, code=self.code)
