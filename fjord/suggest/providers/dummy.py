import logging

from fjord.suggest import Link, Suggester

PROVIDER = 'dummy'
PROVIDER_VERSION = 1


logger = logging.getLogger('i.dummysuggester')


class DummySuggester(Suggester):
    def load(self):
        logger.debug('dummy load')

    def get_suggestions(self, feedback, request=None):
        logger.debug('dummy get_suggestions')
        return [
            Link(
                provider=PROVIDER,
                provider_version=PROVIDER_VERSION,
                summary=u'summary {0}'.format(feedback.description),
                description=u'description {0}'.format(feedback.description),
                url=feedback.url
            )
        ]
