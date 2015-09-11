__all__ = ['get_suggesters', 'Link', 'Suggester']

default_app_config = 'fjord.suggest.apps.SuggestConfig'


# List of loaded Suggester instances
_SUGGESTERS = []


def get_suggesters():
    """Returns Suggester instances"""
    return list(_SUGGESTERS)


from fjord.suggest.base import Link, Suggester
