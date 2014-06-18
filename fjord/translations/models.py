from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from dennis.translator import Translator
from statsd import statsd

from .gengo_utils import (
    FjordGengo,
    GengoMachineTranslationFailure,
    GengoUnknownLanguage,
    GengoUnsupportedLanguage,
)
from .utils import locale_equals_language
from fjord.journal.models import Record
from fjord.journal.utils import j_error, j_info


class SuperModel(models.Model):
    """Model used for unit tests

    It's really difficult to define a model in the test suite used
    just for testing without a lot of shenanigans with South and the
    db, so intead we define a "real" model, but only use it for
    testing.

    """
    locale = models.CharField(max_length=5)
    desc = models.CharField(blank=True, default=u'', max_length=100)
    trans_desc = models.CharField(blank=True, default=u'', max_length=100)


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

    def log_info(self, instance, action='translate', msg=u'', metadata=None):
        metadata = metadata or {}

        record = j_info(
            app='translations',
            src=self.name,
            action=action,
            msg=msg,
            instance=instance,
            metadata=metadata
        )

    def log_error(self, instance, action='translate', msg=u'', metadata=None):
        metadata = metadata or {}

        j_error(
            app='translations',
            src=self.name,
            action=action,
            msg=msg,
            instance=instance,
            metadata=metadata
        )


# ---------------------------------------------------------
# Fake translation system
# ---------------------------------------------------------

class FakeTranslator(TranslationSystem):
    """Translates by uppercasing text"""
    name = 'fake'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        setattr(instance, dst_field, getattr(instance, src_field).upper())
        instance.save()
        self.log_info(instance=instance, action='translate', msg='success')

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
            self.log_info(instance=instance, action='translate', msg='success')


# ---------------------------------------------------------
# Gengo machine translator system AI 9000 of doom
# ---------------------------------------------------------

class GengoMachineTranslator(TranslationSystem):
    """Translates using Gengo machine translation"""
    name = 'gengo_machine'

    def translate(self, instance, src_lang, src_field, dst_lang, dst_field):
        text = getattr(instance, src_field)

        gengo_api = FjordGengo()
        try:
            lc_src = gengo_api.guess_language(text)
            if not locale_equals_language(instance.locale, lc_src):
                self.error(
                    instance,
                    action='guess-language',
                    msg='locale "{0}" != guessed language "{1}"'.format(
                        instance.locale, lc_src),
                    text=text)

            translated = gengo_api.get_machine_translation(
                instance.id, lc_src, 'en', text)

            if translated:
                setattr(instance, dst_field, translated)
                instance.save()
                metadata = {
                    'locale': instance.locale,
                    'length': len(text),
                    'body': text[:50].encode('utf-8')
                }
                self.log_info(instance, action='translate', msg='success',
                              metadata=metadata)
                statsd.incr('translation.gengo_machine.success')

            else:
                metadata = {
                    'locale': instance.locale,
                    'length': len(text),
                    'body': text[:50].encode('utf-8')
                }
                self.log_error(instance, action='translate',
                               msg='did not translate', metadata=metadata)
                statsd.incr('translation.gengo_machine.failure')

        except GengoUnknownLanguage as exc:
            # FIXME: This might be an indicator that this response is
            # spam. At some point p, we can write code to account for
            # that.
            metadata = {
                'locale': instance.locale,
                'length': len(text),
                'body': text[:50].encode('utf-8')
            }
            self.log_error(instance, action='guess-language', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.unknown')

        except GengoUnsupportedLanguage as exc:
            # FIXME: This is a similar boat to GengoUnknownLanguage
            # where for now, we're just going to ignore it because I'm
            # not sure what to do about it and I'd like more data.
            metadata = {
                'locale': instance.locale,
                'length': len(text),
                'body': text[:50].encode('utf-8')
            }
            self.log_error(instance, action='translate', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.unsupported')

        except GengoMachineTranslationFailure:
            # FIXME: For now, if we have a machine translation
            # failure, we're just going to ignore it and move on.
            metadata = {
                'locale': instance.locale,
                'length': len(text),
                'body': text[:50].encode('utf-8')
            }
            self.log_error(instance, action='translate', msg=unicode(exc),
                           metadata=metadata)
            statsd.incr('translation.gengo_machine.failure')


# ---------------------------------------------------------
# Gengo human translator system
# ---------------------------------------------------------

STATUS_CREATED = 'created'
STATUS_IN_PROGRESS = 'in-progress'
STATUS_COMPLETE = 'complete'

STATUS_CHOICES = (
    (STATUS_CREATED, STATUS_CREATED),
    (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
    (STATUS_COMPLETE, STATUS_COMPLETE)
)


class GengoJob(models.Model):
    """Represents a job for the Gengo human translation system"""
    # Generic foreign key to the instance this record is about
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    # Source and destination fields for the translation
    src_field = models.CharField(max_length=50)
    dst_field = models.CharField(max_length=50)

    # Source and destination languages
    src_lang = models.CharField(default=u'', blank=True, max_length=10)
    dst_lang = models.CharField(default=u'', blank=True, max_length=10)

    # Status of the job and the order it's tied to
    status = models.CharField(
        choices=STATUS_CHOICES, default=STATUS_CREATED, max_length=12)
    order = models.ForeignKey('translations.GengoOrder', null=True)

    # When the Gengo job is submitted, we generate an "id" that ties
    # it back to our system. This is that id.
    custom_data = models.CharField(default=u'', blank=True, max_length=100)

    created = models.DateTimeField(default=datetime.now())

    def log(self, action, metadata):
        j_info(
            app='translations',
            src='gengo_human',
            action=action,
            msg='job event',
            metadata=metadata
        )

    def records(self):
        return Record.objects.records(self)


class GengoOrder(models.Model):
    """Represents a Gengo translation order which contains multiple jobs"""
    order_id = models.CharField(max_length=100)
    status = models.CharField(
        choices=STATUS_CHOICES, default=STATUS_CREATED, max_length=12)

    # When the record was submitted to Gengo. This isn't necessarily
    # when the record was created, so we explicitly populate it.
    submitted = models.DateTimeField(null=True)

    def log(self, action, metadata):
        j_info(
            app='translations',
            src='gengo_human',
            action=action,
            msg='order event',
            metadata=metadata
        )

    def records(self):
        return Record.objects.records(self)
