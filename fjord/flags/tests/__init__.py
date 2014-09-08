import factory

from fjord.flags.models import Flag


class FlagFactory(factory.DjangoModelFactory):
    class Meta:
        model = Flag

    name = 'test-abuse'
