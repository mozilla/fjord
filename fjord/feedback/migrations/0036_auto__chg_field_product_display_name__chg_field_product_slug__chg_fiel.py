# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Product.display_name'
        db.alter_column(u'feedback_product', 'display_name', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'Product.slug'
        db.alter_column(u'feedback_product', 'slug', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'Product.db_name'
        db.alter_column(u'feedback_product', 'db_name', self.gf('django.db.models.fields.CharField')(max_length=50))

    def backwards(self, orm):

        # Changing field 'Product.display_name'
        db.alter_column(u'feedback_product', 'display_name', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'Product.slug'
        db.alter_column(u'feedback_product', 'slug', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'Product.db_name'
        db.alter_column(u'feedback_product', 'db_name', self.gf('django.db.models.fields.CharField')(max_length=20))

    models = {
        u'feedback.product': {
            'Meta': {'object_name': 'Product'},
            'db_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_file': ('django.db.models.fields.CharField', [], {'default': "u'noimage.png'", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'on_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'on_picker': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'translation_system': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'feedback.response': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Response'},
            'api': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'browser': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'browser_platform': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'browser_version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'device': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'happy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'rating': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'translated_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'url': ('fjord.base.models.EnhancedURLField', [], {'max_length': '200', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        u'feedback.responsecontext': {
            'Meta': {'object_name': 'ResponseContext'},
            'data': ('fjord.base.models.JSONObjectField', [], {'default': '{}'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opinion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['feedback.Response']"})
        },
        u'feedback.responseemail': {
            'Meta': {'object_name': 'ResponseEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opinion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['feedback.Response']"})
        }
    }

    complete_apps = ['feedback']