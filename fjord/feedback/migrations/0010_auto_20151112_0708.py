# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0009_auto_20151111_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='user_agent',
            field=models.CharField(max_length=1000, blank=True),
        ),
    ]
