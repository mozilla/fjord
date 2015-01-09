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
            ('response_version', self.gf('django.db.models.fields.IntegerField')()),
            ('updated_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('person_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('survey_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['heartbeat.Survey'], to_field='name')),
            ('flow_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('question_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('question_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('variation_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('max_score', self.gf('django.db.models.fields.FloatField')()),
            ('flow_began_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_offered_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_voted_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_engaged_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('channel', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('build_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('partner_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('profile_age', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('profile_usage', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('addons', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('is_test', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('slop', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
        ))
        db.send_create_signal(u'heartbeat', ['Answer'])

        # Adding model 'Survey'
        db.create_table(u'heartbeat_survey', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'heartbeat', ['Survey'])


    def backwards(self, orm):
        # Deleting model 'Answer'
        db.delete_table(u'heartbeat_answer')

        # Deleting model 'Survey'
        db.delete_table(u'heartbeat_survey')


    models = {
        u'heartbeat.answer': {
            'Meta': {'object_name': 'Answer'},
            'addons': ('fjord.base.models.JSONObjectField', [], {'default': "u'{}'"}),
            'build_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'flow_began_ts': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'flow_engaged_ts': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'flow_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'flow_offered_ts': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'flow_voted_ts': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'max_score': ('django.db.models.fields.FloatField', [], {}),
            'partner_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'person_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'profile_age': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'profile_usage': ('fjord.base.models.JSONObjectField', [], {'default': "u'{}'"}),
            'question_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'question_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'response_version': ('django.db.models.fields.IntegerField', [], {}),
            'score': ('django.db.models.fields.FloatField', [], {}),
            'slop': ('fjord.base.models.JSONObjectField', [], {'default': "u'{}'"}),
            'survey_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['heartbeat.Survey']", 'to_field': "'name'"}),
            'updated_ts': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'variation_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'heartbeat.survey': {
            'Meta': {'object_name': 'Survey'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['heartbeat']