from functools import wraps

from elasticsearch import ElasticsearchException
from statsd import statsd


def es_error_statsd(fun):
    """Sends a statsd ping for every ES error

    .. Note::

       This has to be the inner-most decorator so that it can see the
       Elasticsearch error, do its statsd thing and re-raise it for
       error handling.

    """
    @wraps(fun)
    def _es_error_statsd(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except ElasticsearchException:
            statsd.incr('elasticsearch.error')
            raise

    return _es_error_statsd


def to_class_path(cls):
    """Returns class path for a class

    Takes a class and returns the class path which is composed of the
    module plus the class name. This can be reversed later to get the
    class using ``from_class_path``.

    :returns: string

    >>> from fjord.search.models import Record
    >>> to_class_path(Record)
    'fjord.search.models:Record'

    """
    return ':'.join([cls.__module__, cls.__name__])


def from_class_path(cls_path):
    """Returns the class

    Takes a class path and returns the class for it.

    :returns: varies

    >>> from_class_path('fjord.search.models:Record')
    <Record ...>

    """
    module_path, cls_name = cls_path.split(':')
    module = __import__(module_path, fromlist=[cls_name])
    return getattr(module, cls_name)
