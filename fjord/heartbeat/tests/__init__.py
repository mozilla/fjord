import factory

from fjord.heartbeat.models import Answer, Poll


class PollFactory(factory.DjangoModelFactory):
    class Meta:
        model = Poll

    slug = 'firefox-is-great'
    description = ''
    status = ''
    enabled = True


class AnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Answer

    locale = 'en-US'
    platform = 'Linux'
    product = 'Firefox'
    version = '30.0a1'
    channel = 'stable'

    extra = {}

    poll = factory.SubFactory(PollFactory)
    answer = '1'
