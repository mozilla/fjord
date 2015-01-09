# -*- coding: utf-8 -*-
import os

from south.v2 import DataMigration

from django.conf import settings

# Using parse_ua here because this data migration will be moot in a
# month.
from fjord.base.browsers import parse_ua

# Copy of fjord.feedback.models.Response.infer_product.
def infer_product(browser):
    platform = browser.platform

    # FIXME: This is hard-coded.
    if platform == u'Firefox OS':
        return u'Firefox OS'

    elif platform == u'Android':
        return u'Firefox for Android'

    elif platform in (u'', u'Unknown'):
        return u''

    return u'Firefox'


class Migration(DataMigration):

    def forwards(self, orm):
        # Note: You need to re-index after running this data migration!

        # Look at all responses that weren't submitted by the API
        # (that's a different code path) that don't have a version,
        # but do have a product and a user agent.
        resps = (orm.Response.objects
                 .filter(version='')
                 .exclude(api=1)
                 .exclude(product='')
                 .exclude(user_agent=''))

        total_count = resps.count()
        total_saved = 0

        for resp in resps:
            browser = parse_ua(resp.user_agent)
            if resp.product == infer_product(browser):
                resp.version = browser.browser_version
                resp.save()
                total_saved += 1

        if not getattr(settings, 'TEST'):
            print (os.path.basename(__file__),
                   'Fixed version on {0} of {1} responses'.format(
                       total_saved, total_count))

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")

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
    symmetrical = True
