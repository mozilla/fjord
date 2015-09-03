# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import fjord.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('trigger', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='triggerrule',
            name='keywords',
            field=fjord.base.models.ListField(help_text='Key words and phrases to match.', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='triggerrule',
            name='locales',
            field=fjord.base.models.ListField(help_text='Locales to match.', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='triggerrule',
            name='products',
            field=models.ManyToManyField(help_text='Products to match.', to='feedback.Product', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='triggerrule',
            name='versions',
            field=fjord.base.models.ListField(help_text='Versions to match. Allows for prefix matches for strings that end in "*".', blank=True),
            preserve_default=True,
        ),
    ]
