from datetime import datetime, timedelta

from django.db import models

from dennis.translator import Translator
from statsd import statsd

from fjord.base.models import ModelBase, JSONObjectField
from .gengo_utils import (
    FjordGengo,
    GengoMachineTranslationFailure,
    GengoUnknownLanguage,
    GengoUnsupportedLanguage,
)


RECORD_INFO = u'info'
RECORD_ERROR = u'error'


class RecordManager(models.Manager):
    @classmethod
    def _log(cls, type_, src, action, msg, instance=None, metadata=None):
        from .utils import compose_key
        key = compose_key(instance) if instance else u''
        metadata = metadata or {}
        rec = Record(type=type_, src=src, action=action, msg=msg, key=key,
                     metadata=metadata)
        rec.save()
        return rec

    @classmethod
    def info(cls, src, action, msg, instance=None, metadata=None):
        return cls._log(RECORD_INFO, src, action, msg, instance, metadata)

    @classmethod
    def error(cls, src, action, msg, instance=None, metadata=None):
        return cls._log(RECORD_ERROR, src, action, msg, instance, metadata)

    def recent(self):
        return self.filter(created__gte=datetime.now() - timedelta(days=14))


class Record(ModelBase):
    """Defines an audit record for something that happened in translations"""

    TYPE_CHOICES = [
        (RECORD_INFO, RECORD_INFO),
        (RECORD_ERROR, RECORD_ERROR),
    ]

    # What component was running (e.g. "gengo-machine", "dennis", ...)
    src = models.CharField(max_length=50)

    # The type of this message (e.g. "info", "error", ...)
    type = models.CharField(choices=TYPE_CHOICES, max_length=20)

    # What happened to create this entry (e.g. "guess-language",
    # "translate", ...)
    action = models.CharField(max_length=20)

    # The message details (e.g. "unknown language", "unsupported language"
    msg = models.CharField(max_length=255)

    # The class:id key for the instance
    key = models.CharField(default=u'', blank=True, max_length=50)

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
        return u'<Record {data} {msg}>'.format(
            u':'.join([self.src, self.type, self.action]),
            self.msg)


_translation_systems = {}


def get_translation_systems():
    """Returns translation systems map

    """
    return _translation_systems


def get_translation_system_choices():
    """Returns a tuple of (value, display-name) tuples for Choices field

    This inserts a "no choice" choice at the beginning, too, the value of
    which is the empty string.

    """
    choices = [(key, key) for key in _translation_systems.keys()]
    choices.insert(0, (u'', u'None'))
    return tuple(choices)


class TranslationSystemMeta(type):
    """Metaclass to register TranslationSystem subclasses"""
    def __new__(cls, name, bases, attrs):
        new_cls = super(TranslationSystemMeta, cls).__new__(
            cls, name, bases, attrs)
        if new_cls.name:
            _translation_systems[new_cls.name] = new_cls
        return new_cls


class TranslationSystem(object):
    """Translation system base class

    All translation system plugins should subclass this. They should
    additionally do the following:

    1. set the name property to something unique
    2. implement translate method

    See FakeTranslator and DennisTranslator for sample
    implementations.

    """
    __metaclass__ = TranslationSystemMeta

    # Name of this translation system
    name = ''

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        """Implement this to translation fields on an instance

        This translates in-place.

        If this is an asynchronous system, then this can either push
        the text to be translated now or queue the text to be pushed
        later in a batch of things to be translated.

        """
        raise NotImplementedError()

    def push_translations(self):
        """Implement this to do any work required to push translations

        This is for asynchronous systems that take a batch of translations,
        perform some work, and then return results some time later.

        Print any status text to stdout.

        """
        raise NotImplementedError()

    def pull_translations(self):
        """Implement this to do any work required to pull translations

        This is for asynchronous systems that take a batch of translations,
        perform some work, and then return results some time later.

        Print any status text to stdout.

        """
        raise NotImplementedError()


# ---------------------------------------------------------
# Fake translation system
# ---------------------------------------------------------

class FakeTranslator(TranslationSystem):
    """Translates by uppercasing text"""
    name = 'fake'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        setattr(instance, dst_field, getattr(instance, src_field).upper())
        instance.save()
        Record.objects.info(
            src=self.name, action='translate',
            msg='success',
            instance=instance)

    def pull_translations(self):
        # This is a no-op for testing purposes.
        pass

    def push_translations(self):
        # This is a no-op for testing purposes.
        pass


# ---------------------------------------------------------
# Dennis translation system
# ---------------------------------------------------------

class DennisTranslator(TranslationSystem):
    """Translates using shouty and anglequote"""
    name = 'dennis'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        text = getattr(instance, src_field)
        if text:
            pipeline = ['shouty', 'anglequote']
            translated = Translator([], pipeline).translate_string(text)
            setattr(instance, dst_field, translated)
            instance.save()
            Record.objects.info(
                src=self.name, action='translate',
                msg='success',
                instance=instance)


# ---------------------------------------------------------
# Gengo machine translator system AI 9000 of doom
# ---------------------------------------------------------

class GengoMachineTranslator(TranslationSystem):
    """Translates using Gengo machine translation"""
    name = 'gengo_machine'

    def info(self, instance, action='translate', msg=u'', text=u''):
        msg = msg.encode('utf-8')
        text = text or u''

        Record.objects.info(
            src=self.name,
            action=action,
            msg=msg,
            instance=instance,
            metadata={
                'locale': instance.locale,
                'length': len(text),
                'body': text[:50].encode('utf-8'),
            })

    def error(self, instance, action='translate', msg=u'', text=u''):
        msg = msg.encode('utf-8')
        text = text or u''

        Record.objects.error(
            src=self.name,
            action=action,
            msg=msg,
            instance=instance,
            metadata={
                'locale': instance.locale,
                'length': len(text),
                'body': text[:50].encode('utf-8'),
            })

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        text = getattr(instance, src_field)

        gengo_api = FjordGengo()
        try:
            translated = gengo_api.get_machine_translation(instance.id, text)
            if translated:
                setattr(instance, dst_field, translated)
                instance.save()
                self.info(instance, action='translate', msg='success',
                          text=text)
                statsd.incr('translation.gengo_machine.success')

            else:
                self.error(instance, action='translate',
                           msg='did not translate', text=text)
                statsd.incr('translation.gengo_machine.failure')

        except GengoUnknownLanguage as exc:
            # FIXME: This might be an indicator that this response is
            # spam. At some point p, we can write code to account for
            # that.
            self.error(instance, action='guess-language', msg=unicode(exc),
                       text=text)
            statsd.incr('translation.gengo_machine.unknown')

        except GengoUnsupportedLanguage as exc:
            # FIXME: This is a similar boat to GengoUnknownLanguage
            # where for now, we're just going to ignore it because I'm
            # not sure what to do about it and I'd like more data.
            self.error(instance, action='translate', msg=unicode(exc),
                       text=text)
            statsd.incr('translation.gengo_machine.unsupported')

        except GengoMachineTranslationFailure:
            # FIXME: For now, if we have a machine translation
            # failure, we're just going to ignore it and move on.
            self.error(instance, action='translate', msg=unicode(exc),
                       text=text)
            statsd.incr('translation.gengo_machine.failure')
