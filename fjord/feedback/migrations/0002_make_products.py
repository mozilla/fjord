# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def make_products(apps, schema_editor):
    # Create the current set of products
    Product = apps.get_model('feedback', 'Product')

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Firefox',
        db_name=u'Firefox',
        slug=u'firefox',
        browser_data_browser=u'Firefox',
        browser=u'Firefox',
        on_dashboard=True,
        on_picker=True)

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Firefox for Android',
        db_name=u'Firefox for Android',
        slug=u'android',
        browser=u'Firefox for Android',
        on_dashboard=True,
        on_picker=True)

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Firefox OS',
        db_name=u'Firefox OS',
        slug=u'fxos',
        browser=u'Firefox OS',
        on_dashboard=True,
        on_picker=True)

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Firefox Developer',
        db_name=u'Firefox dev',
        slug=u'firefoxdev',
        browser_data_browser=u'Firefox',
        browser=u'Firefox',
        on_dashboard=False,
        on_picker=True)

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Loop',
        db_name=u'Loop',
        slug=u'loop',
        on_dashboard=False,
        on_picker=False)

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Firefox 64',
        db_name=u'Firefox 64',
        slug=u'firefox64',
        browser_data_browser=u'Firefox',
        browser=u'Firefox',
        on_dashboard=False,
        on_picker=False)

    Product.objects.create(
        enabled=True,
        notes=u'',
        display_name=u'Firefox Metro',
        db_name=u'Firefox Metro',
        slug=u'metrofirefox',
        on_dashboard=False,
        on_picker=False)


def remove_products(apps, schema_editor):
    Product = apps.get_model('feedback', 'Product')
    Product.objects.filter(slug__in=[
        'firefox',
        'android',
        'fxos',
        'firefoxdev',
        'loop',
        'firefox64',
        'metrofirefox']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(make_products, remove_products),
    ]
