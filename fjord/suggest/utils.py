import logging

from fjord.suggest import get_providers


logger = logging.getLogger('i.suggest')


def get_suggestions(response):
    """Given a feedback response, returns an ordered list of suggestions"""
    suggestions = []

    for prov in get_providers():
        try:
            suggestions.extend(prov.get_suggestions(response))
        except Exception:
            logger.exception('Error in provider {0}'.format(
                prov.__class__.__name__))

    return suggestions
