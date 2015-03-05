# -*- coding: utf-8 -*-
"""Adds "received_ts" field to Heartbeat Answer model.

"""
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0005_auto_20150225_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='received_ts',
            field=models.DateTimeField(default=datetime.datetime(2011, 9, 1, 9, 0), help_text='Time the server received the last update packet', auto_now=True),
            preserve_default=False,
        ),
    ]
