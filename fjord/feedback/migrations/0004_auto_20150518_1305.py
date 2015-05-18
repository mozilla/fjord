# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0003_delete_empty_desc_feedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='description',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
