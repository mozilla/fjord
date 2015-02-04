# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def make_waffles(apps, schema_editor):
    # Create the waffle flags and switches we currently need.
    Flag = apps.get_model('waffle', 'Flag')
    Switch = apps.get_model('waffle', 'Switch')

    Flag.objects.create(
        name='feedbackdev',
        everyone=False,
        superusers=False,
        staff=False,
        authenticated=False,
        rollout=False,
        note='',
        testing=False)

    Flag.objects.create(
        name='ditchchart',
        everyone=False,
        superusers=False,
        staff=False,
        authenticated=False,
        rollout=False,
        note='',
        testing=False)

    Switch.objects.create(
        name='gengosystem',
        note='Enables/disables Gengo API usage',
        active=True)

    Flag.objects.create(
        name='thankyou',
        everyone=False,
        superusers=False,
        staff=False,
        authenticated=False,
        rollout=False,
        note='',
        testing=False)


def remove_waffles(apps, schema_editor):
    # Create the waffle flags and switches we currently need.
    Flag = apps.get_model('waffle', 'Flag')
    Switch = apps.get_model('waffle', 'Switch')

    Flag.objects.filter(
        name__in=['feedbackdev', 'ditchchart', 'thankyou']).delete()
    Switch.objects.filter(name='gengosystem').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
        ('waffle', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(make_waffles, remove_waffles),
    ]
