import logging

from fjord.suggest import Link, Provider


logger = logging.getLogger('i.dummyprovider')


class DummyProvider(Provider):
    def load(self):
        logger.debug('dummy load')

    def get_suggestions(self, response):
        logger.debug('dummy get_suggestions')
        return [
            Link(
                type_=u'dummy',
                summary=u'summary {0}'.format(response.description),
                description=u'description {0}'.format(response.description),
                url=response.url
            )
        ]
