# -*- coding: utf-8 -*-
"""Delete duplicate answers for (survey_id, person_id, flow_id).

We're in the process of making that unique and in order to do
that, there can't be any existing non-unique data.

We're deleting the earliest iterations of these, but in all the cases
I looked at, the early and later ones were identical.

"""
from __future__ import unicode_literals

from django.db import models, migrations


def no_op(apps, schema_editor):
    pass


def delete_hb_dupes(apps, schema_editor):
    """Go through and delete duplicate (survey, person, flow) answers"""
    Answer = apps.get_model('heartbeat', 'Answer')

    fields = ('id', 'survey_id', 'person_id', 'flow_id')

    for ans in Answer.objects.values(*fields).order_by('id'):
        count = (Answer.objects
                 .filter(
                     survey_id=ans['survey_id'],
                     person_id=ans['person_id'],
                     flow_id=ans['flow_id']
                 )
                 .count())

        if count > 1:
            print 'Deleting answer id {}'.format(ans['id'])
            # If there's more than one of this, we delete this
            # one because it's the oldest.
            Answer.objects.filter(id=ans['id']).delete()
            

class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0003_auto_20150225_1216'),
    ]

    operations = [
        # Note: This can't be backed out, but for the sake of testing
        # and convenience, we provide a no-op.
        migrations.RunPython(delete_hb_dupes, reverse_code=no_op),
    ]
