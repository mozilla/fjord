# -*- coding: utf-8 -*-
"""Deletes all feedback that have a description that's an empty
string.

"""

from __future__ import unicode_literals

import sys

from django.db import models, migrations


def delete_feedback(apps, schema_editor):
    """Delete all feedback with an empty description"""
    Response = apps.get_model('feedback', 'Response')
    qs = Response.objects.filter(description='')
    count = qs.count()
    if count > 0:
        qs.delete()
        if 'test' not in sys.argv:
            print 'Deleted {0} responses'.format(count)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('feedback', '0002_make_products'),
    ]

    operations = [
        migrations.RunPython(delete_feedback, noop)
    ]
