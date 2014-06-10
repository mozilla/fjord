from django.db import models

from fjord.base.util import instance_to_key


class FakeModel(models.Model):
    locale = models.CharField(max_length=2)
    desc = models.CharField(blank=True, default=u'', max_length=100)
    trans_desc = models.CharField(blank=True, default=u'', max_length=100)

    def generate_translation_jobs(self, system=None):
        return [
            (instance_to_key(self), system, self.locale, 'desc',
             'en-US', 'trans_desc')
        ]
