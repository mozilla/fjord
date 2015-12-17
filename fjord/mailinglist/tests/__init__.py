import factory
from factory import fuzzy

from fjord.mailinglist.models import MailingList


class MailingListFactory(factory.DjangoModelFactory):
    class Meta:
        model = MailingList

    name = fuzzy.FuzzyText(length=10)
    members = u''
