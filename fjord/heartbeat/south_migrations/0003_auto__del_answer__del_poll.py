# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Answer'
        db.delete_table(u'heartbeat_answer')

        # Deleting model 'Poll'
        db.delete_table(u'heartbeat_poll')


    def backwards(self, orm):
        # Adding model 'Answer'
        db.create_table(u'heartbeat_answer', (
            ('product', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('extra', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['heartbeat.Poll'], to_field='slug')),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('channel', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'heartbeat', ['Answer'])

        # Adding model 'Poll'
        db.create_table(u'heartbeat_poll', (
            ('status', self.gf('django.db.models.fields.CharField')(default=u'', max_length=1000, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default=u'', blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'heartbeat', ['Poll'])


    models = {
        
    }

    complete_apps = ['heartbeat']