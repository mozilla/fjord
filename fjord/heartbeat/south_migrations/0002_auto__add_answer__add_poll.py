# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Answer'
        db.create_table(u'heartbeat_answer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('product', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('channel', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('extra', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['heartbeat.Poll'], to_field='slug')),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'heartbeat', ['Answer'])

        # Adding model 'Poll'
        db.create_table(u'heartbeat_poll', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(default=u'', blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default=u'', max_length=1000, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'heartbeat', ['Poll'])


    def backwards(self, orm):
        # Deleting model 'Answer'
        db.delete_table(u'heartbeat_answer')

        # Deleting model 'Poll'
        db.delete_table(u'heartbeat_poll')


    models = {
        u'heartbeat.answer': {
            'Meta': {'object_name': 'Answer'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'extra': ('fjord.base.models.JSONObjectField', [], {'default': "u'{}'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['heartbeat.Poll']", 'to_field': "'slug'"}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'heartbeat.poll': {
            'Meta': {'object_name': 'Poll'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '1000', 'blank': 'True'})
        }
    }

    complete_apps = ['heartbeat']
