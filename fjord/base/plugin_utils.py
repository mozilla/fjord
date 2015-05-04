import logging

from django.utils.module_loading import import_string


def load_providers(provider_list, logger=None):
    """Loads providers in the provided list

    :arg provider_list: list of Python dotted module paths; the provider
        class should be the last name in the path

    :arg logger: (optional) logger to log to for errors

    :returns: list of providers.

    >>> load_providers(['some.path.Class', 'some.other.path.OtherClass'])
    [<Class>, <OtherClass>]

    .. Note::

       All exceptions when importing and loading providers are
       swallowed and logged as errors. Providers that don't import or
       don't load are not returned in the return list.

    """
    if logger is None:
        logger = logging.getLogger('i.plugin_utils')

    provider_objects = []
    for provider in provider_list:
        try:
            # Import the class and instantiate it.
            provider_objects.append(import_string(provider)())
        except Exception:
            logger.exception('Provider {0} failed to import'.format(provider))

    providers = []
    for provider in provider_objects:
        try:
            provider.load()
            providers.append(provider)
        except Exception:
            logger.exception('Provider {0} failed to load'.format(provider))

    return providers
