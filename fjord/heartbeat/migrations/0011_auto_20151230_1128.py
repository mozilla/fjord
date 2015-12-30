# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def add_heartbeat_health(apps, schema_editor):
    MailingList = apps.get_model('mailinglist', 'MailingList')
    ml = MailingList.objects.create(name='heartbeat_health')
    ml.save()


def remove_heartbeat_health(apps, schema_editor):
    MailingList = apps.get_model('mailinglist', 'MailingList')
    MailingList.objects.filter(name='heartbeat_health').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('heartbeat', '0010_auto_20150806_0712'),
        ('mailinglist', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_heartbeat_health, remove_heartbeat_health),
    ]
