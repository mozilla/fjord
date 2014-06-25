# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'GengoOrder.submitted'
        db.delete_column(u'translations_gengoorder', 'submitted')

        # Adding field 'GengoOrder.created'
        db.add_column(u'translations_gengoorder', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 6, 25, 0, 0)),
                      keep_default=False)

        # Adding field 'GengoOrder.completed'
        db.add_column(u'translations_gengoorder', 'completed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'GengoJob.completed'
        db.add_column(u'translations_gengojob', 'completed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'GengoOrder.submitted'
        db.add_column(u'translations_gengoorder', 'submitted',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Deleting field 'GengoOrder.created'
        db.delete_column(u'translations_gengoorder', 'created')

        # Deleting field 'GengoOrder.completed'
        db.delete_column(u'translations_gengoorder', 'completed')

        # Deleting field 'GengoJob.completed'
        db.delete_column(u'translations_gengojob', 'completed')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'translations.gengojob': {
            'Meta': {'object_name': 'GengoJob'},
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 25, 0, 0)'}),
            'dst_field': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'dst_lang': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['translations.GengoOrder']", 'null': 'True'}),
            'src_field': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'src_lang': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '10', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '12'})
        },
        u'translations.gengoorder': {
            'Meta': {'object_name': 'GengoOrder'},
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 25, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'in-progress'", 'max_length': '12'})
        },
        u'translations.supermodel': {
            'Meta': {'object_name': 'SuperModel'},
            'desc': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'trans_desc': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['translations']