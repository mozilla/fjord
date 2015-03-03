# -*- coding: utf-8 -*-
"""Add start_time and end_time to Alert model"""
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0002_alertflavor_allowed_tokens'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='end_time',
            field=models.DateTimeField(help_text='Timestamp for the end of this event', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alert',
            name='start_time',
            field=models.DateTimeField(help_text='Timestamp for the beginning of this event', null=True, blank=True),
            preserve_default=True,
        ),
    ]
