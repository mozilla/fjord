# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0005_product_display_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='response',
            name='rating',
        ),
    ]
