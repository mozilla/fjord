__all__ = ['build_redirect_url', 'get_redirectors', 'Redirector',
           'RedirectParseError']


default_app_config = 'fjord.redirector.apps.RedirectorConfig'


# List of loaded redirector instances
_REDIRECTORS = []


def get_redirectors():
    """Returns redirector providers

    :returns: list of Redirector instances

    """
    return list(_REDIRECTORS)


from .base import build_redirect_url, Redirector, RedirectParseError
