# -*- coding: utf-8 -*-
"""Add unique_together for (person_id, survey_id, flow_id) so that we
don't have duplicate Answers with that tuple.

"""
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('heartbeat', '0004_auto_20150225_1232'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('person_id', 'survey_id', 'flow_id')]),
        ),
    ]
