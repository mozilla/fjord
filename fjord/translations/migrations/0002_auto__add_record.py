# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Record'
        db.create_table(u'translations_record', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('src', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('msg', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('key', self.gf('django.db.models.fields.CharField')(default=u'', max_length=50, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('metadata', self.gf('fjord.base.models.JSONObjectField')()),
        ))
        db.send_create_signal(u'translations', ['Record'])


    def backwards(self, orm):
        # Deleting model 'Record'
        db.delete_table(u'translations_record')


    models = {
        u'translations.record': {
            'Meta': {'object_name': 'Record'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'metadata': ('fjord.base.models.JSONObjectField', [], {}),
            'msg': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'src': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['translations']