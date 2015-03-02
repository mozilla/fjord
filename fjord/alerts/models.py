from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

import pytz
from rest_framework import fields
from rest_framework import serializers

from fjord.api_auth.models import Token
from fjord.base.models import ModelBase


class AlertFlavor(ModelBase):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        help_text=u'Used by the API for posting')
    description = models.TextField(
        blank=True, default=u'',
        help_text=u'Explanation of what this alert flavor entails')
    more_info = models.CharField(
        max_length=200, blank=True, default=u'',
        help_text=u'A url to more information about this alert flavor')
    default_severity = models.IntegerField(
        help_text=(u'Default severity for alerts of this flavor '
                   '(0: low, 10: high)'))

    allowed_tokens = models.ManyToManyField(
        Token,
        blank=True,
        help_text=u'Tokens that are permitted to emit this flavor'
    )

    enabled = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def is_permitted(self, token):
        """Return whether given token is permitted to emit to this flavor"""
        return token.enabled and token in self.allowed_tokens.all()


class Alert(ModelBase):
    severity = models.IntegerField(
        help_text=u'0-10 severity of the alert (0: low, 10: high)')
    flavor = models.ForeignKey(AlertFlavor)
    summary = models.TextField(
        help_text=u'Brief summary of the alert--like the subject of an email')
    description = models.TextField(
        blank=True, default=u'',
        help_text=u'Complete text-based description of the alert')
    emitter_name = models.CharField(
        max_length=100,
        help_text=u'Unique name for the emitter that created this')
    emitter_version = models.IntegerField(
        help_text=u'Integer version number for the emitter')
    start_time = models.DateTimeField(
        null=True, blank=True,
        help_text=u'Timestamp for the beginning of this event')
    end_time = models.DateTimeField(
        null=True, blank=True,
        help_text=u'Timestamp for the end of this event')
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'{} {} {} {}'.format(self.severity, self.flavor.slug,
                                     self.summary, str(self.created))


class Link(ModelBase):
    alert = models.ForeignKey(Alert)
    name = models.CharField(
        max_length=200, blank=True, default=u'',
        help_text=u'Brief name of the link')
    url = models.URLField(
        help_text=u'URL of the link')

    def __unicode__(self):
        return self.url


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


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('name', 'url')


class AlertSerializer(serializers.ModelSerializer):
    flavor = serializers.SlugRelatedField(slug_field='slug')
    # Note: This is read-only because we handle the POST side
    # manually.
    links = LinkSerializer(source='link_set', many=True, read_only=True)

    start_time = UTCDateTimeField(required=False)
    end_time = UTCDateTimeField(required=False)

    class Meta:
        model = Alert
