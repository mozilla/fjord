# -*- coding: utf-8 -*-
"""Set received_ts using the value in updated_ts. It's not the same
thing, but it's "close enough" for an initial value where we don't
have anything better to base it on.

This is just like 0007, but since I screwed that one up, we have to
do it again.

"""
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.db import models, migrations

import pytz


def no_op(apps, schema_editor):
    pass


def set_received_ts(apps, schema_editor):
    """Sets received_ts based on updated_ts"""
    Answer = apps.get_model('heartbeat', 'Answer')

    qs = Answer.objects.filter(received_ts=datetime(2011, 9, 1, 9, 0))
    for ans in qs:
        # Note: Answer.updated_ts is milliseconds since epoch. We're
        # assuming it's in UTC, so we convert it to server time.
        dt = datetime.fromtimestamp(ans.updated_ts / 1000)

        # Apply UTC
        utc_tz = pytz.timezone('UTC')
        dt = utc_tz.localize(dt)

        # Then switch to server time
        local_tz = pytz.timezone(settings.TIME_ZONE)
        dt = dt.astimezone(local_tz)

        ans.received_ts = dt
        ans.save()


class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0007_auto_20150305_1119'),
    ]

    operations = [
        # Note: This can't be backed out, but for the sake of testing
        # and convenience, we provide a no-op.
        migrations.RunPython(set_received_ts, reverse_code=no_op),
    ]
