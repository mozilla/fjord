class Provider(object):
    """Suggestion provider class

    Implement ``load`` and ``get_suggestions`` methods.

    """
    def load(self):
        """Implement this to perform any startup work"""
        pass

    def get_suggestions(self, response):
        """Implement this to return suggestions for a given piece of
        feedback

        :arg response: feedback Response

        :returns: list of Link instances

        .. Note::

           This should be re-entrant and threadsafe.

        """
        raise NotImplementedError


class Link(object):
    """Represents a single Link"""
    def __init__(self, type_, summary, url, description):
        self.type_ = type_
        self.summary = summary
        self.url = url
        self.description = description
