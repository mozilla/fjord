# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import fjord.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app', models.CharField(max_length=50)),
                ('src', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=20, choices=[('info', 'info'), ('error', 'error')])),
                ('action', models.CharField(max_length=20)),
                ('msg', models.CharField(max_length=255)),
                ('object_id', models.PositiveIntegerField(null=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('metadata', fjord.base.models.JSONObjectField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
