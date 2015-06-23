import datetime

from django.db import models

from fjord.base.models import ModelBase


class Record(ModelBase):
    """Indexing record."""
    STATUS_NEW = 0
    STATUS_IN_PROGRESS = 1
    STATUS_FAIL = 2
    STATUS_SUCCESS = 3

    STATUS_CHOICES = (
        (STATUS_NEW, 'new'),
        (STATUS_IN_PROGRESS, 'in progress'),
        (STATUS_FAIL, 'done - fail'),
        (STATUS_SUCCESS, 'done - success'),
    )

    batch_id = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)
    message = models.CharField(max_length=255, blank=True)

    def delta(self):
        """Return the timedelta."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def _complete(self, status, msg='Done'):
        self.end_time = datetime.datetime.now()
        self.status = status
        self.message = msg

    def mark_fail(self, msg):
        """Mark as failed.

        :arg msg: the error message it failed with

        """
        self._complete(self.STATUS_FAIL, msg)
        self.save()

    def mark_success(self, msg='Success'):
        """Mark as succeeded.

        :arg msg: success message if any

        """
        self._complete(self.STATUS_SUCCESS, msg)
        self.save()

    @classmethod
    def outstanding(cls):
        """Return queryset of outstanding records."""
        return cls.objects.filter(status__in=[
            cls.STATUS_NEW, cls.STATUS_IN_PROGRESS])

    def __unicode__(self):
        return '%s:%s%s' % (self.batch_id, self.name, self.status)
