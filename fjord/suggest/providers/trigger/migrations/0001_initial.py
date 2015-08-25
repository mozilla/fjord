# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import fjord.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0006_remove_response_rating'),
    ]

    operations = [
        migrations.CreateModel(
            name='TriggerRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(help_text='Required: One-word unique slug for this trigger rule. Used in redirection urls and GA event tracking. Users will see this. Do not change once it is live!', unique=True)),
                ('title', models.CharField(help_text='Required: Title of the suggestion--best to keep it a short action phrase.', max_length=255)),
                ('description', models.TextField(help_text='Required: Summary of suggestion--best to keep it a short paragraph.')),
                ('url', models.URLField(help_text='Required: URL for the suggestion. This should be locale-independent if possible.')),
                ('sortorder', models.IntegerField(default=5, help_text='Required: Allows you to dictate which trigger rules are more important and thus show up first in a list of trigger rules suggestions.')),
                ('is_enabled', models.BooleanField(default=False)),
                ('locales', fjord.base.models.ListField(help_text='Comma-separated list of locale values to match or empty to match all locales.', blank=True)),
                ('keywords', fjord.base.models.ListField(help_text='Key words and phrases (in quotes) each on a separate line or empty to match all feedback.', blank=True)),
                ('versions', fjord.base.models.ListField(help_text='Comma delimited list of versions to match or empty to match all versions. Use * at the end to match anything after that point. For example "38*" matches all version 38 releases.', blank=True)),
                ('url_exists', models.NullBooleanField(default=None, help_text='Has a url, does not have a url or do not care.')),
                ('products', models.ManyToManyField(help_text='List of products to match or none to match all feedback.', to='feedback.Product', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
