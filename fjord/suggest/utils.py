import logging

from fjord.suggest import get_suggesters


logger = logging.getLogger('i.suggest')


def get_suggestions(feedback):
    """Given a feedback response, returns an ordered list of suggestions"""
    suggestions = []

    for prov in get_suggesters():
        try:
            suggestions.extend(prov.get_suggestions(feedback))
        except Exception:
            logger.exception('Error in provider {0}'.format(
                prov.__class__.__name__))

    return suggestions
