# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Flag'
        db.delete_table(u'flags_flag')

        # Removing M2M table for field responses on 'Flag'
        db.delete_table('flags_flag_responses')

        # Deleting model 'Store'
        db.delete_table(u'flags_store')


    def backwards(self, orm):
        # Adding model 'Flag'
        db.create_table(u'flags_flag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'flags', ['Flag'])

        # Adding M2M table for field responses on 'Flag'
        db.create_table(u'flags_flag_responses', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('flag', models.ForeignKey(orm[u'flags.flag'], null=False)),
            ('response', models.ForeignKey(orm[u'feedback.response'], null=False))
        ))
        db.create_unique(u'flags_flag_responses', ['flag_id', 'response_id'])

        # Adding model 'Store'
        db.create_table(u'flags_store', (
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('classifier', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('key', self.gf('django.db.models.fields.TextField')()),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'flags', ['Store'])


    models = {
        
    }

    complete_apps = ['flags']