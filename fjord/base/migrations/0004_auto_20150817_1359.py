# -*- coding: utf-8 -*-
"""Remove thankyou waffle flag from Flag model data"""
from __future__ import unicode_literals

from django.db import models, migrations


def remove_thankyou_waffle(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    Flag.objects.filter(name='thankyou').delete()


def add_thankyou_waffle(apps, schema_editor):
    # Note: This matches the data in 0002_make_waffles.py except
    # enables it for Everyone because that's the current reality.
    Flag = apps.get_model('waffle', 'Flag')
    Flag.objects.create(
        name='thankyou',
        everyone=True,
        superusers=False,
        staff=False,
        authenticated=False,
        rollout=False,
        note='',
        testing=False)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_remove_ditchchart_waffle_flag'),
    ]

    operations = [
        migrations.RunPython(remove_thankyou_waffle, add_thankyou_waffle),
    ]
