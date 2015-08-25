import factory

from fjord.journal.models import Record


class RecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = Record
