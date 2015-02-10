# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import fjord.base.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('experiment_version', models.CharField(max_length=50)),
                ('response_version', models.IntegerField()),
                ('updated_ts', models.BigIntegerField(default=0)),
                ('person_id', models.CharField(max_length=50)),
                ('flow_id', models.CharField(max_length=50)),
                ('question_id', models.CharField(max_length=50)),
                ('question_text', models.TextField()),
                ('variation_id', models.CharField(max_length=100)),
                ('score', models.FloatField(null=True, blank=True)),
                ('max_score', models.FloatField(null=True, blank=True)),
                ('flow_began_ts', models.BigIntegerField(default=0)),
                ('flow_offered_ts', models.BigIntegerField(default=0)),
                ('flow_voted_ts', models.BigIntegerField(default=0)),
                ('flow_engaged_ts', models.BigIntegerField(default=0)),
                ('platform', models.CharField(default='', max_length=50, blank=True)),
                ('channel', models.CharField(default='', max_length=50, blank=True)),
                ('version', models.CharField(default='', max_length=50, blank=True)),
                ('locale', models.CharField(default='', max_length=50, blank=True)),
                ('build_id', models.CharField(default='', max_length=50, blank=True)),
                ('partner_id', models.CharField(default='', max_length=50, blank=True)),
                ('profile_age', models.BigIntegerField(null=True, blank=True)),
                ('profile_usage', fjord.base.models.JSONObjectField(blank=True)),
                ('addons', fjord.base.models.JSONObjectField(blank=True)),
                ('extra', fjord.base.models.JSONObjectField(blank=True)),
                ('is_test', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('enabled', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(default=b'', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='answer',
            name='survey_id',
            field=models.ForeignKey(to='heartbeat.Survey', db_column=b'survey_id', to_field=b'name'),
            preserve_default=True,
        ),
    ]
