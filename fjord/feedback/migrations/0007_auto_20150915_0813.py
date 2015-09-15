# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0006_remove_response_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='responseemail',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]
