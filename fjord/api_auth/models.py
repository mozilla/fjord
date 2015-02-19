from uuid import uuid4

from django.db import models

from fjord.base.models import ModelBase


class Token(ModelBase):
    token = models.CharField(
        max_length=32, primary_key=True,
        help_text=(
            u'API token to use for authentication. Click on SAVE AND '
            u'CONTINUE EDITING. The token will be generated and you can copy '
            u'and paste it.'
        )
    )
    summary = models.CharField(
        max_length=200,
        help_text=u'Brief explanation of what will use this token')
    enabled = models.BooleanField(default=False)
    disabled_reason = models.TextField(
        blank=True, default=u'',
        help_text=u'If disabled, explanation of why.')
    contact = models.CharField(
        max_length=200, blank=True, default=u'',
        help_text=(
            u'Contact information for what uses this token. Email address, etc'
        )
    )
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'{} {} {}'.format(self.summary, self.enabled, self.token)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super(Token, self).save(*args, **kwargs)

    def generate_token(self):
        return uuid4().hex
