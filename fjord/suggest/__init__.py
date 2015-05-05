__all__ = ['get_providers', 'Link', 'Provider']

default_app_config = 'fjord.suggest.apps.SuggestConfig'


# List of loaded provider classes
_PROVIDERS = []


def get_providers():
    """Returns suggestion providers

    :returns: list of Provider

    """
    return list(_PROVIDERS)


from .base import Link, Provider
