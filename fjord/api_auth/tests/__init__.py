import factory

from fjord.api_auth.models import Token


class TokenFactory(factory.DjangoModelFactory):
    class Meta:
        model = Token

    summary = u'foo token'
    enabled = True
