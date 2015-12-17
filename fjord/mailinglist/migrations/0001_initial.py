# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MailingList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Unique name to identify the mailing list', unique=True, max_length=100)),
                ('members', models.TextField(default='', help_text='List of email addresses for the list--one per line. You can do blank lines. # and everything after that character on the line denotes a comment.', blank=True)),
            ],
        ),
    ]
