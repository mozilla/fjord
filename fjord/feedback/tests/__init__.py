import factory

from fjord.base import browsers
from fjord.feedback.models import (
    Product,
    Response,
    ResponseContext,
    ResponseEmail
)


USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:17.0) Gecko/17.0 Firefox/17.0'


class ProductFactory(factory.DjangoModelFactory):
    class Meta:
        model = Product

    display_name = u'Firefox'
    db_name = factory.LazyAttribute(lambda a: a.display_name)
    notes = u''
    slug = u'firefox'

    enabled = True
    on_dashboard = True
    on_picker = True


class ResponseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Response

    happy = True,
    url = u''
    description = u'So awesome!'

    user_agent = USER_AGENT
    browser = factory.LazyAttribute(
        lambda a: browsers.parse_ua(a.user_agent).browser)
    browser_version = factory.LazyAttribute(
        lambda a: browsers.parse_ua(a.user_agent).browser_version)
    platform = factory.LazyAttribute(
        lambda a: browsers.parse_ua(a.user_agent).platform)

    product = factory.LazyAttribute(
        lambda a: Response.infer_product(
            browsers.parse_ua(a.user_agent)))
    channel = u'stable'
    version = factory.LazyAttribute(
        lambda a: browsers.parse_ua(a.user_agent).browser_version)
    locale = u'en-US'


class ResponseEmailFactory(factory.DjangoModelFactory):
    class Meta:
        model = ResponseEmail

    opinion = factory.SubFactory(ResponseFactory)
    email = 'joe@example.com'


class ResponseContextFactory(factory.DjangoModelFactory):
    class Meta:
        model = ResponseContext

    opinion = factory.SubFactory(ResponseFactory)
    data = '{}'
