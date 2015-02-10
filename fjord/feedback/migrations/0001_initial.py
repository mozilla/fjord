# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import fjord.base.models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True)),
                ('notes', models.CharField(default='', max_length=255, blank=True)),
                ('display_name', models.CharField(max_length=50)),
                ('db_name', models.CharField(max_length=50)),
                ('slug', models.CharField(max_length=50)),
                ('on_dashboard', models.BooleanField(default=True)),
                ('on_picker', models.BooleanField(default=True)),
                ('image_file', models.CharField(default='noimage.png', max_length=100, null=True, blank=True)),
                ('translation_system', models.CharField(blank=True, max_length=20, null=True, choices=[('', 'None'), (b'gengo_machine', b'gengo_machine'), (b'dennis', b'dennis'), (b'gengo_human', b'gengo_human'), (b'fake', b'fake')])),
                ('browser_data_browser', models.CharField(default='', help_text='Grab browser data for browser product', max_length=100, blank=True)),
                ('browser', models.CharField(default='', help_text='User agent inferred browser for this product if any', max_length=30, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('happy', models.BooleanField(default=True)),
                ('rating', models.PositiveIntegerField(null=True)),
                ('url', fjord.base.models.EnhancedURLField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('translated_description', models.TextField(blank=True)),
                ('category', models.CharField(default='', max_length=50, null=True, blank=True)),
                ('product', models.CharField(max_length=30, blank=True)),
                ('platform', models.CharField(max_length=30, blank=True)),
                ('channel', models.CharField(max_length=30, blank=True)),
                ('version', models.CharField(max_length=30, blank=True)),
                ('locale', models.CharField(max_length=8, blank=True)),
                ('country', models.CharField(default='', max_length=4, null=True, blank=True)),
                ('manufacturer', models.CharField(max_length=255, blank=True)),
                ('device', models.CharField(max_length=255, blank=True)),
                ('api', models.IntegerField(null=True, blank=True)),
                ('user_agent', models.CharField(max_length=255, blank=True)),
                ('browser', models.CharField(max_length=30, blank=True)),
                ('browser_version', models.CharField(max_length=30, blank=True)),
                ('browser_platform', models.CharField(max_length=30, blank=True)),
                ('source', models.CharField(default='', max_length=100, null=True, blank=True)),
                ('campaign', models.CharField(default='', max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResponseContext',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', fjord.base.models.JSONObjectField()),
                ('opinion', models.ForeignKey(to='feedback.Response')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResponseEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
                ('opinion', models.ForeignKey(to='feedback.Response')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResponsePI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', fjord.base.models.JSONObjectField()),
                ('opinion', models.ForeignKey(to='feedback.Response')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
