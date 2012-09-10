# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Record'
        db.create_table('search_record', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('batch_id', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('search', ['Record'])


    def backwards(self, orm):
        # Deleting model 'Record'
        db.delete_table('search_record')


    models = {
        'search.record': {
            'Meta': {'object_name': 'Record'},
            'batch_id': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['search']