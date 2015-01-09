# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Simple'
        db.delete_table('feedback_simple')

        # Deleting model 'SimpleEmail'
        db.delete_table('feedback_simpleemail')

        # Adding model 'Response'
        db.create_table('feedback_response', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('prodchan', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('happy', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('user_agent', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('browser', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('browser_version', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('manufacturer', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('device', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('feedback', ['Response'])

        # Adding model 'ResponseEmail'
        db.create_table('feedback_responseemail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('opinion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feedback.Response'])),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal('feedback', ['ResponseEmail'])


    def backwards(self, orm):
        # Adding model 'Simple'
        db.create_table('feedback_simple', (
            ('prodchan', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('browser_version', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('device', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('manufacturer', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('user_agent', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('browser', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('happy', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('feedback', ['Simple'])

        # Adding model 'SimpleEmail'
        db.create_table('feedback_simpleemail', (
            ('opinion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feedback.Simple'])),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('feedback', ['SimpleEmail'])

        # Deleting model 'Response'
        db.delete_table('feedback_response')

        # Deleting model 'ResponseEmail'
        db.delete_table('feedback_responseemail')


    models = {
        'feedback.response': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Response'},
            'browser': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'browser_version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'device': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'happy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'prodchan': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'feedback.responseemail': {
            'Meta': {'object_name': 'ResponseEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opinion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feedback.Response']"})
        }
    }

    complete_apps = ['feedback']