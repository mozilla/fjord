# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Answer'
        db.delete_table(u'heartbeat_answer')


    def backwards(self, orm):
        # Adding model 'Answer'
        db.create_table(u'heartbeat_answer', (
            ('response_version', self.gf('django.db.models.fields.IntegerField')()),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('locale', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('variation_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('is_test', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('partner_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('build_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('flow_offered_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('slop', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('profile_usage', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('flow_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('person_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('channel', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('profile_age', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_engaged_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('question_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('max_score', self.gf('django.db.models.fields.FloatField')()),
            ('flow_voted_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_began_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('survey_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['heartbeat.Survey'], to_field='name')),
            ('updated_ts', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('addons', self.gf('fjord.base.models.JSONObjectField')(default=u'{}')),
            ('question_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'heartbeat', ['Answer'])


    models = {
        u'heartbeat.survey': {
            'Meta': {'object_name': 'Survey'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['heartbeat']