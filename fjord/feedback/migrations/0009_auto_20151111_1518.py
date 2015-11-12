# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import fjord.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0008_auto_20151014_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='url',
            field=fjord.base.models.EnhancedURLField(max_length=1000, blank=True),
        ),
    ]
