# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def add_gengo_balance(apps, schema_editor):
    MailingList = apps.get_model('mailinglist', 'MailingList')
    ml = MailingList.objects.create(name='gengo_balance')
    ml.save()


def remove_gengo_balance(apps, schema_editor):
    MailingList = apps.get_model('mailinglist', 'MailingList')
    MailingList.objects.filter(name='gengo_balance').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0002_gengojob_tier'),
        ('mailinglist', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_gengo_balance, remove_gengo_balance),
    ]
