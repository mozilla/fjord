# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_auth', '0001_initial'),
        ('alerts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertflavor',
            name='allowed_tokens',
            field=models.ManyToManyField(help_text='Tokens that are permitted to emit this flavor', to='api_auth.Token', blank=True),
            preserve_default=True,
        ),
    ]
