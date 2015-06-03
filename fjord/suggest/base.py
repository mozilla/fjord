class Suggester(object):
    """Suggestion provider class

    Implement ``load`` and ``get_suggestions`` methods.

    """
    def load(self):
        """Implement this to perform any startup work"""
        pass

    def get_suggestions(self, feedback, request=None):
        """Implement this to return suggestions for a given piece of feedback

        :arg feedback: feedback Response
        :arg request: the HTTP request or None

        :returns: list of Link instances

        .. Note::

           This should be re-entrant and threadsafe.

        """
        raise NotImplementedError


class Link(object):
    """Represents a single Link"""
    def __init__(self, provider, provider_version, cssclass, summary,
                 url, description):
        self.provider = provider
        self.provider_version = provider_version
        self.cssclass = cssclass
        self.summary = summary
        self.url = url
        self.description = description
