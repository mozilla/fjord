# -*- coding: utf-8 -*-
import os
import re
from south.v2 import DataMigration
from django.conf import settings

# copied and slimmed down from fjord/base/browsers.py
GECKO_TO_FIREFOXOS_VERSION = {
    '18.0': '1.0',
    '18.1': '1.1',
    '26.0': '1.2'
}


def get_browser_parts(ua):
    """Return browser parts portion of user agent"""
    match = re.match(r'^Mozilla[^(]+\(([^)]+)\) (.+)', ua)

    if match is None:
        return []

    # The rest is space seperated A/B pairs. Pull out both sides of
    # the slash.
    # Result: [['Gecko', '14.0'], ['Firefox', '14.0.2']]
    browser_parts = [p.split('/') for p in match.group(2).split(' ')]

    return browser_parts


class Migration(DataMigration):
    def forwards(self, orm):
        working_set = orm.Response.objects.filter(product=u'Firefox OS')

        for resp in working_set:
            parts = get_browser_parts(resp.user_agent)
            for part in parts:
                if 'Gecko' in part and len(part) > 1:
                    fxos_version = GECKO_TO_FIREFOXOS_VERSION.get(part[1])
                    if fxos_version is not None:
                        resp.version = fxos_version
                        resp.browser_version = fxos_version
                        resp.save()

        if not getattr(settings, 'TEST'):
            print os.path.basename(__file__), '{0} fixed'.format(working_set.count())

    def backwards(self, orm):
        working_set = orm.Response.objects.filter(product=u'Firefox OS')

        for resp in working_set:
            parts = get_browser_parts(resp.user_agent)
            for part in parts:
                if 'Firefox' in part and len(part) > 1:
                    fx_version = part[1]
                    if fx_version is not None:
                        if len(fx_version.split('.')) == 2:
                            fx_version = fx_version + '.0'
                        resp.version = fx_version
                        resp.browser_version = fx_version
                        resp.save()

        if not getattr(settings, 'TEST'):
            print os.path.basename(__file__), '{0} unfixed'.format(working_set.count())

    models = {
        'feedback.response': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Response'},
            'browser': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'browser_version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'device': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'happy': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'prodchan': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'translated_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'feedback.responseemail': {
            'Meta': {'object_name': 'ResponseEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opinion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feedback.Response']"})
        }
    }

    complete_apps = ['feedback']
    symmetrical = True
