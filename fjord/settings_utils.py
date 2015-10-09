"""
This module holds utility functions for settings files. Generally, you
only need to use ``config``.

Example::

    DEBUG = config('DEBUG', default=True, type_='bool')

"""
import os
import urlparse


NO_VALUE = object()


def parse_list_of_str(val):
    """Parses a comma-separated list of strings"""
    return val.split(',')


def parse_bool(val):
    """Parses a bool

    Handles a series of values, but you should probably standardize on
    "true" and "false".

    """
    true_vals = ('t', 'true', 'yes', 'y')
    false_vals = ('f', 'false', 'no', 'n')

    val = val.lower()
    if val in true_vals:
        return True
    if val in false_vals:
        return False

    raise ValueError('%s is not a valid bool value' % val)


def parse_database_url(val):
    """Parses a database url

    Format::

        mysql://USER:PASSWORD@HOST:PORT/NAME

    For example::

        mysql://fjord:password@localhost:5431/fjord

    """
    if not val:
        return

    url_parts = urlparse.urlparse(val)

    if url_parts.scheme != 'mysql':
        raise ConfigurationError('Unsupported cache backend. Supported: mysql')

    return {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': url_parts.path[1:],
        'USER': url_parts.username,
        'PASSWORD': url_parts.password,
        'HOST': url_parts.hostname.lower(),
        'PORT': url_parts.port,
        'CHARSET': 'utf8',
        'COLLATION': 'utf8_general_ci',
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB',
            'use_unicode': True,
        },
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATIONS': 'utf8_general_ci',
        }
    }


def parse_cache_url(val):
    """Parses a cache url

    Format::

        BACKEND://LOCATION/PREFIX


    For example::

        locmem://
        memcached://localhost:11211/fjord

    """
    if not val:
        return

    url_parts = urlparse.urlparse(val)

    cache_types = {
        'locmem': 'django.core.cache.backends.locmem.LocMemCache',
        'memcached': 'django.core.cache.backends.memcached.MemcachedCache'
    }

    try:
        backend = cache_types[url_parts.scheme]
    except KeyError:
        raise ConfigurationError('Unsupported cache backend. Supported: ' %
                                 ', '.join(cache_types.keys()))

    return {
        'BACKEND': backend,
        'LOCATION': url_parts.netloc,
        'KEY_PREFIX': url_parts.path[1:]
    }


class ConfigurationError(Exception):
    pass


def config(envvar, default=NO_VALUE, type_='str', raise_error=False):
    """Returns a parsed value from the environment

    :arg envvar: the environment variable name
    :arg default: the default value (if any)
    :arg type_: the type of this value--determines the parser to use
        for converting it from a string
    :arg raise_error: True if you want a lack of value to raise a
        ``ConfigurationError``

    Examples::

        DEBUG = config('DEBUG', default=True, type_='bool')
        DATABASES = {'default': config('DATABASE_URL', type_='database_url')}
        ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost',
                               type_='list_of_str')

    """
    types = {
        'str': str,
        'int': int,
        'float': float,
        'bool': parse_bool,
        'database_url': parse_database_url,
        'cache_url': parse_cache_url,
        'list_of_str': parse_list_of_str,
    }

    parser = types[type_]

    # Check the environment for the specified variable and use that
    val = os.environ.get(envvar, NO_VALUE)
    if val is not NO_VALUE:
        return parser(val)

    # If there's a default, use that
    if default is not NO_VALUE:
        return parser(default)

    # No value specified and no default, so raise an error to the user
    if raise_error:
        msg = '%s requires a value of type %s' % (envvar, type_)
        raise ConfigurationError(msg)
