# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0009_answer_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='channel',
            field=models.CharField(default='', max_length=50, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='answer',
            name='country',
            field=models.CharField(default='', max_length=4, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='answer',
            name='locale',
            field=models.CharField(default='', max_length=50, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='answer',
            name='received_ts',
            field=models.DateTimeField(help_text='Time the server received the last update packet', auto_now=True, db_index=True),
            preserve_default=True,
        ),
    ]
