from .exceptions import NoSuchSystem
from .models import get_translation_systems


def compose_key(instance):
    """Given an instance, returns a key

    :arg instance: The model instance to generate a key for

    :returns: A string representing that specific instance

    .. Note::

       This uses the id attribute of the model instance.

       That's good enough for my needs, but we might need to think about
       changing this if we make this a library.

    """
    cls = instance.__class__
    return ':'.join([cls.__module__, cls.__name__, str(instance.id)])


def decompose_key(key):
    """Given a key, returns the instance

    :raises DoesNotExist: if the instance doesn't exist
    :raises ImportError: if there's an import error
    :raises AttributeError: if the class doesn't exist in the module

    """
    module_path, cls_name, id_ = key.split(':')
    module = __import__(module_path, fromlist=[cls_name])
    cls = getattr(module, cls_name)
    instance = cls.objects.get(id=int(id_))

    return instance


def translate(instance, system, src_lang, src_field, dst_lang, dst_field):
    """Translates specified field using specified system

    :arg instance: A model instance with fields to be translated
    :arg system: The name of the system to be used to do the translation
    :arg src_lang: The language to translate from
    :arg src_field: The name of the source field
    :arg dst_lang: The language to translate to
    :arg dst_field: The name of the destination field

    If the method is synchronous, then this will translate the field
    value and stick it in the translated field immediately.

    If the method is asynchronous, then this will return and the
    translated field will be filled in at some unspecified time.

    """
    # Get the translation system class.
    TranslationSystem = get_translation_systems().get(system)
    if not TranslationSystem:
        raise NoSuchSystem(
            '{0} is not a valid translation system'.format(system))

    # Instantiate the translate system class and translate this text!
    trans_system = TranslationSystem()
    trans_system.translate(instance, src_lang, src_field, dst_lang, dst_field)
