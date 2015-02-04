# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_analyzers_group(apps, schema_editor):
    # First we need to create a content type because there are no
    # models in this app.
    ContentType = apps.get_model('contenttypes', 'ContentType')
    analytics_content_type = ContentType.objects.create(
        name='dashboard',
        app_label='analytics',
        model='unused')

    # Then we create a permission attached to that content type.
    Permission = apps.get_model('auth', 'Permission')
    view_perm = Permission.objects.create(
        name='View analytics dashboard',
        content_type=analytics_content_type,
        codename='can_view_dashboard')

    # And finally we create a group and give it the permission above.
    Group = apps.get_model('auth', 'Group')
    analyzers_group = Group.objects.create(name='analyzers')
    analyzers_group.permissions.add(view_perm)


def remove_analyzers_group(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')

    Group.objects.filter(name='analyzers').delete()
    Permission.objects.filter(codename='can_view_dashboard').delete()
    ContentType.objects.filter(app_label='analytics', model='unused').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_analyzers_group, remove_analyzers_group),
    ]
