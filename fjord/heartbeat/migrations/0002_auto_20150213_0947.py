# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='description',
            field=models.TextField(default=b'', help_text='Informal description of the survey so we can tell them apart', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='survey',
            name='name',
            field=models.CharField(help_text='Unique name for the survey. e.g. heartbeat-question-1', unique=True, max_length=100),
            preserve_default=True,
        ),
    ]
