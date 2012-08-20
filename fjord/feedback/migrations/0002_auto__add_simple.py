# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Simple'
        db.create_table('feedback_simple', (
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
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('feedback', ['Simple'])


    def backwards(self, orm):
        # Deleting model 'Simple'
        db.delete_table('feedback_simple')


    models = {
        'feedback.simple': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Simple'},
            'browser': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'browser_version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'happy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'prodchan': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['feedback']