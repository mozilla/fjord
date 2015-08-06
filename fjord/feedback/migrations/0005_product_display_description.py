# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0004_auto_20150518_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='display_description',
            field=models.TextField(default='', help_text='Displayed description of the product. This will be localized. Should be short.', blank=True),
            preserve_default=True,
        ),
    ]
