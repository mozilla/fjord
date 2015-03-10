# -*- coding: utf-8 -*-
"""Remove ditchchart waffle flag from Flag model data"""
from __future__ import unicode_literals

from django.db import migrations


def remove_ditchchart_waffle(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    Flag.objects.filter(name='ditchchart').delete()


def add_ditchchart_waffle(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    Flag.objects.create(
        name='ditchchart',
        everyone=False,
        superusers=False,
        staff=False,
        authenticated=False,
        rollout=False,
        note='',
        testing=False)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_make_waffles'),
    ]

    operations = [
        migrations.RunPython(remove_ditchchart_waffle, add_ditchchart_waffle),
    ]
