# -*- coding: utf-8 -*-
"""
Add country to heartbeat Answer table.
"""
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0008_auto_20150305_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='country',
            field=models.CharField(default='', max_length=4, null=True, blank=True),
            preserve_default=True,
        ),
    ]
