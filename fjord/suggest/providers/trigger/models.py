import re

from django.db import models
from django.utils.lru_cache import lru_cache

from fjord.base.models import ListField, ModelBase
from fjord.feedback.models import Product


class TriggerRuleManager(models.Manager):
    def all_enabled(self):
        return self.filter(is_enabled=True).order_by('sortorder')


@lru_cache()
def _generate_keywords_regex(keywords):
    """Generates a Regex object to compare with

    * for each keyword
      * converts white space to '\s+'
    * joins the parts to create a middle
    * joins that with empty string bounds
    * compiles it into a Regex and returns it

    :arg keywords: list of unicode strings

    :returns: regex object

    """
    # Make absolutely sure it's a list of unicode strings because
    # crossing the streams is bad.
    assert [isinstance(keyword, unicode) for keyword in keywords]

    def _escape(utext):
        """Escape regexp characters

        This is different than re.escape which escapes everything that
        isn't an alphanumeric character which doesn't work well with
        unicode and also escapes spaces which I don't want because
        we want to convert consecutive spaces to \s+ later.

        """
        chars = r'\/.^$*+?{}()|?<>[]-'
        for c in chars:
            utext = utext.replace(c, u'\\' + c)
        return u''.join(utext)

    keywords = [
        re.sub(ur'\s+', ur'\s+', _escape(keyword))
        for keyword in keywords
    ]
    middle = (
        u'(?:' +
        u'|'.join(keywords) +
        u')'
    )
    # Note: Can't use \b here because we need to be able to find
    # arbitrary strings--not just alphanumeric ones.
    regex = ur'(?:^|\W)' + middle + ur'(?:\W|$)'
    return re.compile(regex, re.IGNORECASE | re.UNICODE)


class TriggerRule(ModelBase):
    # Trigger properties
    slug = models.SlugField(
        unique=True,
        help_text=(
            u'Required: One-word unique slug for this trigger rule. Used '
            u'in redirection urls and GA event tracking. Users will see '
            u'this. Do not change once it is live!'
        )
    )
    title = models.CharField(
        max_length=255,
        help_text=(
            u'Required: Title of the suggestion--best to keep it a short '
            u'action phrase.'
        )
    )
    description = models.TextField(
        help_text=(
            u'Required: Summary of suggestion--best to keep it a short '
            u'paragraph.'
        )
    )
    url = models.URLField(
        help_text=(
            u'Required: URL for the suggestion. This should be '
            u'locale-independent if possible.'
        )
    )
    sortorder = models.IntegerField(
        default=5,
        help_text=(
            u'Required: Allows you to dictate which trigger rules are more '
            u'important and thus show up first in a list of trigger rules '
            u'suggestions.'
        )
    )
    is_enabled = models.BooleanField(default=False)

    # Trigger filters
    locales = ListField(
        blank=True,
        help_text=u'Locales to match.'
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        help_text=u'Products to match.'
    )
    keywords = ListField(
        blank=True,
        help_text=u'Key words and phrases to match.'
    )
    versions = ListField(
        blank=True,
        help_text=(
            u'Versions to match. Allows for prefix matches for strings that '
            u'end in "*".'
        )
    )
    url_exists = models.NullBooleanField(
        default=None,
        blank=True,
        help_text=u'Has a url, does not have a url or do not care.'
    )

    objects = TriggerRuleManager()

    def match_locale(self, locale):
        # Check if this rule matches all locales
        if not self.locales:
            return True

        # Check if there was a locale supplied
        if not locale:
            return False

        # Check if the locale was in the rule
        return locale in self.locales

    def match_version(self, version):
        # Check if this rule matches all versions
        if not self.versions:
            return True

        # Check if there was a version supplied
        if not version:
            return False

        # Check if the version was in the rule accounting for prefixes
        for vers in self.versions:
            if version == vers:
                return True
            if vers.endswith('*') and version.startswith(vers[:-1]):
                return True
        return False

    def match_product(self, product_name):
        # Check if this rule matches all products
        if not self.products.count():
            return True

        # Check if there was a product supplied
        if not product_name:
            return False

        # Check if this product was in the rule
        product_db_names = [prod.db_name for prod in self.products.all()]
        return product_name in product_db_names

    def match_description(self, description):
        if not self.keywords:
            return True

        if not description:
            return False

        regex = _generate_keywords_regex(tuple(self.keywords))
        return regex.search(description) is not None

    def match_url_exists(self, url):
        if self.url_exists is None:
            return True
        return bool(self.url_exists) == bool(url)

    def match(self, feedback):
        """Returns True if specified feedback matches this rule"""
        return (
            self.match_version(feedback.version)
            and self.match_locale(feedback.locale)
            and self.match_product(feedback.product)
            and self.match_description(feedback.description)
            and self.match_url_exists(feedback.url)
        )

    def __unicode__(self):
        return u'{0}'.format(self.title)
