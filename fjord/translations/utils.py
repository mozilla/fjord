from .exceptions import NoSuchSystem


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
    # Have to import this here because of circular import problems.
    from .models import get_translation_systems

    # Get the translation system class.
    TranslationSystem = get_translation_systems().get(system)
    if not TranslationSystem:
        raise NoSuchSystem(
            '{0} is not a valid translation system'.format(system))

    # Instantiate the translate system class and translate this text!
    trans_system = TranslationSystem()
    trans_system.translate(instance, src_lang, src_field, dst_lang, dst_field)


def locale_equals_language(locale, lang):
    """Returns wehther the locale and language are equivalent

    This is pretty goofy because locale != language, but this can be
    used for places where we have the locale the user was visiting the
    site with and a language and determine whether they're "similar"
    or "way off".

    This will help us determine whether we have locales which are
    problematic and address those problems.

    """
    locale_parts = locale.lower().split('-')
    lang_parts = lang.lower().split('-')

    return locale_parts[0] == lang_parts[0]
