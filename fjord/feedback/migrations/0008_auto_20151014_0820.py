# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0007_auto_20150915_0813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='db_name',
            field=models.CharField(help_text='Do not change this after you have created the product. You will orphan all the existing feedback!', max_length=50),
        ),
    ]
