from django.conf import settings

import pytz
from rest_framework import fields
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import APIException


class UTCDateTimeField(fields.DateTimeField):
    """Like DateTimeField, except it is always in UTC in the API"""
    def to_representation(self, value):
        """Convert outgoing datetimes into UTC strings

        Input currently saves everything in Pacific time, but without
        timezone info. So this takes the datetimes and converts them
        from Pacific time to UTC.

        If this situation ever changes, then we'd change
        settings.TIME_ZONE and this should continue to work.

        """
        if value is not None and value.tzinfo is None:
            default_tzinfo = pytz.timezone(settings.TIME_ZONE)
            value = default_tzinfo.localize(value)
            value = value.astimezone(pytz.utc)
        return super(UTCDateTimeField, self).to_representation(value)

    def to_internal_value(self, value):
        """Converts incoming UTC strings to localtime datetimes

        Input currently saves everything in Pacific time, so this
        takes the datetime that super().from_native() produces,
        converts it to localtime and if USE_TZ=False, drops the timezone.

        If this situation ever changes, this should continue to work.

        """
        result = super(UTCDateTimeField, self).to_internal_value(value)

        if result is not None:
            if result.tzinfo is None:
                # We have a timezone-less datetime, so we need to give
                # it a timezone to do the rest of the work. We choose
                # UTC because the API using this is all about UTC.
                result = pytz.utc.localize(result)

            # Convert from whatever timezone it's in to local
            # time.
            local_tzinfo = pytz.timezone(settings.TIME_ZONE)
            result = result.astimezone(local_tzinfo)

            # If USE_TZ = False, drop the timezone
            if not settings.USE_TZ:
                result = result.replace(tzinfo=None)

        return result


class StrictArgumentsMixin(object):
    """DRF Serializer mixin that requires init_data to be a subset of
    fields

    This is for API endpoints that require that all arguments passed in
    are handled. If an argument is specified that doesn't exist, then
    this will raise a ``serializers.ValidationError`` during validation.

    To use::

        from rest_framework import serializers

        from fjord.base.api_utils import StrictArgumentsMixin


        class MySerializer(StrictArgumentMixin, serializers.Serializer):
            ...

    """
    def validate(self, data):
        data = super(StrictArgumentsMixin, self).validate(data)

        # Guarantee that arguments passed in are a subset of possible
        # fields.
        if self.initial_data:
            for key in self.initial_data.keys():
                if key not in self.fields:
                    raise serializers.ValidationError(
                        '"{0}" is not a valid argument.'.format(key)
                    )

        return data


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Not found.'
