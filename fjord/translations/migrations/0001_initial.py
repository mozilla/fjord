# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GengoJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('src_field', models.CharField(max_length=50)),
                ('dst_field', models.CharField(max_length=50)),
                ('src_lang', models.CharField(default='', max_length=10, blank=True)),
                ('dst_lang', models.CharField(default='', max_length=10, blank=True)),
                ('status', models.CharField(default=b'created', max_length=12, choices=[(b'created', b'created'), (b'in-progress', b'in-progress'), (b'complete', b'complete')])),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('completed', models.DateTimeField(null=True, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GengoOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order_id', models.CharField(max_length=100)),
                ('status', models.CharField(default=b'in-progress', max_length=12, choices=[(b'created', b'created'), (b'in-progress', b'in-progress'), (b'complete', b'complete')])),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('completed', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SuperModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('locale', models.CharField(max_length=5)),
                ('desc', models.CharField(default='', max_length=100, blank=True)),
                ('trans_desc', models.CharField(default='', max_length=100, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='gengojob',
            name='order',
            field=models.ForeignKey(to='translations.GengoOrder', null=True),
            preserve_default=True,
        ),
    ]
