# -*- coding: utf-8 -*-
"""Add an index_together for (person, survey, flow).

We do a lot of searching on that trio, so it makes sense to have an
index for it.

"""
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('heartbeat', '0002_auto_20150213_0947'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='answer',
            index_together=set([('person_id', 'survey_id', 'flow_id')]),
        ),
    ]
