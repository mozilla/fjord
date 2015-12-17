from django.db import models

from fjord.base.models import ModelBase


class MailingList(ModelBase):
    name = models.CharField(
        max_length=100, unique=True,
        help_text=u'Unique name to identify the mailing list'
    )
    members = models.TextField(
        blank=True, default=u'',
        help_text=(
            u'List of email addresses for the list--one per line. You '
            u'can do blank lines. # and everything after that character '
            u'on the line denotes a comment.'
        )
    )

    @property
    def recipient_list(self):
        members = []
        for line in self.members.splitlines():
            if '#' in line:
                line = line[:line.find('#')]
            line = line.strip()
            if line:
                members.append(line)
        members.sort()
        return members
