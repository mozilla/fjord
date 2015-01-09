# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SuperModel'
        db.create_table(u'translations_supermodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('desc', self.gf('django.db.models.fields.CharField')(default=u'', max_length=100, blank=True)),
            ('trans_desc', self.gf('django.db.models.fields.CharField')(default=u'', max_length=100, blank=True)),
        ))
        db.send_create_signal(u'translations', ['SuperModel'])


    def backwards(self, orm):
        # Deleting model 'SuperModel'
        db.delete_table(u'translations_supermodel')


    models = {
        u'translations.supermodel': {
            'Meta': {'object_name': 'SuperModel'},
            'desc': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'trans_desc': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['translations']