from datetime import datetime, timedelta

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from fjord.base.models import ModelBase, JSONObjectField


RECORD_INFO = u'info'
RECORD_ERROR = u'error'


class RecordManager(models.Manager):
    @classmethod
    def log(cls, type_, app, src, action, msg, instance=None, metadata=None):
        msg = msg.encode('utf-8')
        metadata = metadata or {}

        rec = Record(
            app=app,
            type=type_,
            src=src,
            action=action,
            content_object=instance,
            msg=msg,
            metadata=metadata
        )
        rec.save()
        return rec

    def recent(self, app):
        return (self
                .filter(app=app)
                .filter(created__gte=datetime.now() - timedelta(days=7)))

    def records(self, instance):
        return (
            self
            .filter(object_id=instance.id,
                    content_type=ContentType.objects.get_for_model(instance))
        )


class Record(ModelBase):
    """Defines an audit record for something that happened in translations"""

    TYPE_CHOICES = [
        (RECORD_INFO, RECORD_INFO),
        (RECORD_ERROR, RECORD_ERROR),
    ]

    # What app does this apply to
    app = models.CharField(max_length=50)

    # What component was running (e.g. "gengo-machine", "dennis", ...)
    src = models.CharField(max_length=50)

    # The type of this message (e.g. "info", "error", ...)
    type = models.CharField(choices=TYPE_CHOICES, max_length=20)

    # What happened to create this entry (e.g. "guess-language",
    # "translate", ...)
    action = models.CharField(max_length=20)

    # The message details in English (e.g. "unknown language",
    # "unsupported language", ...)
    msg = models.CharField(max_length=255)

    # Generic foreign key to the object this record is about if any
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey()

    # When this log entry was created
    created = models.DateTimeField(default=datetime.now)

    # Any metadata related to this entry in the form of a Python dict which
    # is stored as a JSON object
    metadata = JSONObjectField(default=u'{}')

    # Note: This doesn't use django-cache-machine. These objects are
    # mostly for site maintenance purposes and thus we don't really
    # want to be dealing with cache.
    objects = RecordManager()

    def __unicode__(self):
        return u'<Record {key} {msg}>'.format(
            key=u':'.join([self.src, self.type, self.action]),
            msg=self.msg)
