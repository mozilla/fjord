# -*- coding: utf-8 -*-
import os

from django.conf import settings

from south.v2 import DataMigration


class Migration(DataMigration):
    def forwards(self, orm):
        # Get the set of versions that need fixing
        versions = set(orm.Response
                       .objects
                       .filter(version__endswith='.0.0')
                       .values_list('version', flat=True))

        count = 0

        # For the versions that need fixing, update the responses so
        # they have a .0 version rather than a .0.0 version.
        for vers in versions:
            new_vers = vers.replace('.0.0', '.0')
            update_count = (orm.Response
                            .objects
                            .filter(version=vers)
                            .update(version=new_vers))
            count += update_count

            if not getattr(settings, 'TEST'):
                print 'version: %s: %s' % (vers, update_count)

        if not getattr(settings, 'TEST'):
            print (os.path.basename(__file__),
                   'Fixed version on {0} responses'.format(count))

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")

    models = {
        u'feedback.product': {
            'Meta': {'object_name': 'Product'},
            'db_name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'on_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'translation_system': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'feedback.response': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Response'},
            'api': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'browser': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'browser_version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
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
            'prodchan': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'translated_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        u'feedback.responseemail': {
            'Meta': {'object_name': 'ResponseEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opinion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['feedback.Response']"})
        }
    }

    complete_apps = ['feedback']
    symmetrical = True
