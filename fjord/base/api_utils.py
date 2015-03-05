from django.conf import settings

import pytz
from rest_framework import fields


class UTCDateTimeField(fields.DateTimeField):
    """Like DateTimeField, except it is always in UTC in the API"""
    def to_native(self, value):
        """Convert outgoing datetimes into UTC

        Input currently saves everything in Pacific time, so this
        takes the datetimes and converts them from Pacific time to
        UTC.

        If this situation ever changes, then we'd change
        settings.TIME_ZONE and this should continue to work.

        """
        if value is not None and value.tzinfo is None:
            default_tzinfo = pytz.timezone(settings.TIME_ZONE)
            value = default_tzinfo.localize(value)
            value = value.astimezone(pytz.utc)
        return super(UTCDateTimeField, self).to_native(value)

    def from_native(self, value):
        """Converts incoming strings to localtime

        Input currently saves everything in Pacific time, so this
        takes the datetime that super().from_native() produces,
        converts it to localtime and if USE_TZ=False, drops the timezone.

        If this situation ever changes, this should continue to work.

        """
        result = super(UTCDateTimeField, self).from_native(value)

        if result is not None and result.tzinfo is not None:
            # Convert from whatever timezone it's in to local
            # time.
            local_tzinfo = pytz.timezone(settings.TIME_ZONE)
            result = result.astimezone(local_tzinfo)

            # If USE_TZ = False, drop the timezone
            if not settings.USE_TZ:
                result = result.replace(tzinfo=None)
        return result
