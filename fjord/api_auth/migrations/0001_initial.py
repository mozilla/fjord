# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('token', models.CharField(help_text='API token to use for authentication. Click on SAVE AND CONTINUE EDITING. The token will be generated and you can copy and paste it.', max_length=32, serialize=False, primary_key=True)),
                ('summary', models.CharField(help_text='Brief explanation of what will use this token', max_length=200)),
                ('enabled', models.BooleanField(default=False)),
                ('disabled_reason', models.TextField(default='', help_text='If disabled, explanation of why.', blank=True)),
                ('contact', models.CharField(default='', help_text='Contact information for what uses this token. Email address, etc', max_length=200, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
