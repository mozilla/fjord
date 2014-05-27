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
