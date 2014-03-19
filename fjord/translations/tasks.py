from django.db.models.signals import post_save

from celery import task

from .utils import (
    compose_key,
    decompose_key,
    translate
)


@task()
def translate_task(instance_key):
    """Celery task to kick off translation

    :arg instance_key: The key for the instance we're translating

    """
    instance = decompose_key(instance_key)
    jobs = instance.generate_translation_jobs()
    if not jobs:
        return

    # Handle each job
    for key, system, src_lang, src_field, dst_lang, dst_field in jobs:
        instance = decompose_key(key)

        translate(instance, system, src_lang, src_field, dst_lang, dst_field)


def translate_handler(sender, instance=None, created=False, **kwargs):
    """Handles possible translation

    This asks the instance to generate translation jobs. If there
    are translation jobs to do, then this throws them into a celery
    task.

    """
    if not created or instance is None:
        return

    translate_task.delay(compose_key(instance))


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
    uid = str(model_cls) + 'translation'
    post_save.connect(translate_handler, model_cls, dispatch_uid=uid)
    return model_cls
