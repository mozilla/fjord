# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GengoJob'
        db.create_table(u'translations_gengojob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('src_field', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('dst_field', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('src_lang', self.gf('django.db.models.fields.CharField')(default=u'', max_length=10, blank=True)),
            ('dst_lang', self.gf('django.db.models.fields.CharField')(default=u'', max_length=10, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='created', max_length=12)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translations.GengoOrder'], null=True)),
            ('custom_data', self.gf('django.db.models.fields.CharField')(default=u'', max_length=100, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 6, 18, 0, 0))),
        ))
        db.send_create_signal(u'translations', ['GengoJob'])

        # Adding model 'GengoOrder'
        db.create_table(u'translations_gengoorder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('status', self.gf('django.db.models.fields.CharField')(default='created', max_length=12)),
            ('submitted', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'translations', ['GengoOrder'])


    def backwards(self, orm):
        # Deleting model 'GengoJob'
        db.delete_table(u'translations_gengojob')

        # Deleting model 'GengoOrder'
        db.delete_table(u'translations_gengoorder')


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
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 18, 0, 0)'}),
            'custom_data': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'blank': 'True'}),
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '12'}),
            'submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
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