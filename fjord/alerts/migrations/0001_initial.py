# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('severity', models.IntegerField(help_text='0-10 severity of the alert (0: low, 10: high)')),
                ('summary', models.TextField(help_text='Brief summary of the alert--like the subject of an email')),
                ('description', models.TextField(default='', help_text='Complete text-based description of the alert', blank=True)),
                ('emitter_name', models.CharField(help_text='Unique name for the emitter that created this', max_length=100)),
                ('emitter_version', models.IntegerField(help_text='Integer version number for the emitter')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AlertFlavor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(help_text='Used by the API for posting')),
                ('description', models.TextField(default='', help_text='Explanation of what this alert flavor entails', blank=True)),
                ('more_info', models.CharField(default='', help_text='A url to more information about this alert flavor', max_length=200, blank=True)),
                ('default_severity', models.IntegerField(help_text='Default severity for alerts of this flavor (0: low, 10: high)')),
                ('enabled', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', help_text='Brief name of the link', max_length=200, blank=True)),
                ('url', models.URLField(help_text='URL of the link')),
                ('alert', models.ForeignKey(to='alerts.Alert')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='alert',
            name='flavor',
            field=models.ForeignKey(to='alerts.AlertFlavor'),
            preserve_default=True,
        ),
    ]
