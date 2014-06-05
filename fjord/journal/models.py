from datetime import datetime, timedelta

from django.db import models

from fjord.base.models import ModelBase, JSONObjectField
from fjord.base.util import path_to_class


RECORD_INFO = u'info'
RECORD_ERROR = u'error'


class RecordManager(models.Manager):
    @classmethod
    def log(cls, type_, app, src, action, msg, cls_path=u'', obj_id=None,
            instance=None, metadata=None):
        metadata = metadata or {}

        rec = Record(
            app=app,
            type=type_,
            src=src,
            action=action,
            cls_path=cls_path,
            obj_id=obj_id,
            msg=msg,
            metadata=metadata
        )
        rec.save()
        return rec

    def recent(self, app):
        return (self
                .filter(app=app)
                .filter(created__gte=datetime.now() - timedelta(days=14)))


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

    # The class path for the model instance this record applies to (if any)
    # (e.g. 'fjord.feedback.models:Response', ...)
    cls_path = models.CharField(default=u'', blank=True, max_length=100)

    # The id for the model instance in question (if any)
    obj_id = models.IntegerField(null=True)

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

    @property
    def obj(self):
        """Returns the instance this record applies to or None"""
        if self.obj_id is None or not self.cls_path:
            return None

        cls = path_to_class(self.cls_path)
        return cls.objects.get(pk=self.obj_id)
