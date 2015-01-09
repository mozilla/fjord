# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Answer.variation_id'
        db.alter_column(u'heartbeat_answer', 'variation_id', self.gf('django.db.models.fields.CharField')(max_length=100))

    def backwards(self, orm):

        # Changing field 'Answer.variation_id'
        db.alter_column(u'heartbeat_answer', 'variation_id', self.gf('django.db.models.fields.CharField')(max_length=50))

    models = {
        u'heartbeat.answer': {
            'Meta': {'object_name': 'Answer'},
            'addons': ('fjord.base.models.JSONObjectField', [], {'default': '{}', 'blank': 'True'}),
            'build_id': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'channel': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'experiment_version': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'extra': ('fjord.base.models.JSONObjectField', [], {'default': '{}', 'blank': 'True'}),
            'flow_began_ts': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'flow_engaged_ts': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'flow_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'flow_offered_ts': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'flow_voted_ts': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locale': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'max_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'partner_id': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'person_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'platform': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'}),
            'profile_age': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'profile_usage': ('fjord.base.models.JSONObjectField', [], {'default': '{}', 'blank': 'True'}),
            'question_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'question_text': ('django.db.models.fields.TextField', [], {}),
            'response_version': ('django.db.models.fields.IntegerField', [], {}),
            'score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'survey_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['heartbeat.Survey']", 'to_field': "'name'", 'db_column': "'survey_id'"}),
            'updated_ts': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'variation_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'version': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'blank': 'True'})
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