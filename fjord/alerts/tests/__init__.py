import factory

from fjord.alerts.models import Alert, AlertFlavor, Link


class AlertFlavorFactory(factory.DjangoModelFactory):
    class Meta:
        model = AlertFlavor

    name = u'translation balance'
    slug = u'translation-balance'
    description = u'alerts related to translation balance'
    default_severity = 0
    enabled = True


class AlertFactory(factory.DjangoModelFactory):
    class Meta:
        model = Alert

    severity = 0
    flavor = factory.SubFactory(AlertFlavorFactory)
    summary = u'account balance low'
    description = u'the account balance is at $5.'
    emitter_name = u'balance-checker'
    emitter_version = 0


class LinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = Link

    alert = factory.SubFactory(AlertFactory)
    name = u'more info'
    url = u'http://example.com/ou812'
