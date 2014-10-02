from django.db.models.signals import post_save

from celery import task

from fjord.base.utils import key_to_instance
from .utils import translate


@task(rate_limit='60/m')
def translate_task(instance_key, system, src_lang, src_field,
                   dst_lang, dst_field):
    """Celery task to perform a single translation

    .. Note::

       This is rate-limited at 60/m.

       We really want the translate call to be rate-limited based on
       the translation system, but given we're only supporting Gengo
       right now, I'm going to do the rate limiting here across all
       translation systems rather than figure out how to do it just
       for Gengo.

    :arg instance_key: The key for the instance we're translating
    :arg system: The name of the translation system to use
    :arg src_lang: The source language
    :arg src_field: The field in the instance holding the text to
         translate
    :arg dst_lang: The destination language
    :arg dst_field: The field in the instance to shove the translated
        text into

    """
    instance = key_to_instance(instance_key)
    translate(instance, system, src_lang, src_field, dst_lang, dst_field)


def create_translation_tasks(instance, system=None):
    """Generate translation tasks for a given translateable instance"""
    jobs = instance.generate_translation_jobs(system=system)
    if not jobs:
        return []

    for key, system, src_lang, src_field, dst_lang, dst_field in jobs:
        if not getattr(instance, src_field).strip():
            # Don't create a job unless there's something to translate.
            continue

        translate_task.delay(key, system, src_lang, src_field,
                             dst_lang, dst_field)

    return jobs


def translate_handler(sender, instance=None, created=False, **kwargs):
    """post-save handler that generates translation jobs

    This only does translation work on instance creation--not update.

    This asks the instance to generate translation jobs. If there are
    translation jobs to do, then this throws each one into a separate
    celery task.

    """
    if not created or instance is None:
        return

    return create_translation_tasks(instance)


# Set of models registered for translation.
REGISTERED_MODELS = set()


def register_auto_translation(model_cls):
    """Decorator that Registers model class for automatic translation

    The model class has to have a ``generate_translation_jobs`` method
    that takes an instance and generates a list of translation jobs
    that need to be performed.

    A translation job is a tuple in the form::

        (key, system, src_lang, src_field, dst_lang, dst_field)

    The key is some string that uniquely identifies the instance so
    that we can save the data back to the instance later.

    """
    uid = '-'.join([model_cls.__module__, model_cls.__name__, 'translation'])
    post_save.connect(translate_handler, model_cls, dispatch_uid=uid)
    REGISTERED_MODELS.add(model_cls)
    return model_cls
