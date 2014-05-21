from dennis.translator import Translator
from statsd import statsd

from .gengo_utils import (
    FjordGengo,
    GengoMachineTranslationFailure,
    GengoUnknownLanguage,
)


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
            translated = gengo_api.get_machine_translation(instance.id, text)
            if translated:
                setattr(instance, dst_field, translated)
                instance.save()
                statsd.incr('translation.gengo_machine.success')

            else:
                statsd.incr('translation.gengo_machine.failure')

        except GengoUnknownLanguage:
            # FIXME: This might be an indicator that this response is
            # spam. At some point p, we can write code to account for
            # that.
            statsd.incr('translation.gengo_machine.unknown')

        except GengoMachineTranslationFailure:
            # FIXME: For now, if we have a machine translation
            # failure, we're just going to ignore it and move on.
            statsd.incr('translation.gengo_machine.failure')
