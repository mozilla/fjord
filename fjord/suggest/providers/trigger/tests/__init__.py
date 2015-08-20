import factory
from factory.fuzzy import FuzzyText

from fjord.feedback.tests import ProductFactory
from fjord.suggest.providers.trigger.models import TriggerRule


class TriggerRuleFactory(factory.DjangoModelFactory):
    class Meta:
        model = TriggerRule

    slug = FuzzyText()
    title = 'OU812'
    description = 'Oh, you ate one, too?'
    url = 'https://wiki.mozilla.org/Firefox/Input'

    is_enabled = True

    @factory.post_generation
    def products(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for product in extracted:
                self.products.add(product)
