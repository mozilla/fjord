import re

from django.utils.translation import ugettext, ungettext

import jinja2
from jinja2.ext import InternationalizationExtension


def install_gettext():
    """Install gettext into the Jinja2 environment."""
    class Translation(object):
        # We pass this object to jinja so it can use django's gettext
        # implementation.
        ugettext = staticmethod(ugettext)
        ungettext = staticmethod(ungettext)

    import jingo
    jingo.env.install_gettext_translations(Translation)


def strip_whitespace(message):
    return re.compile(r'\s+', re.UNICODE).sub(' ', message).strip()


class MozInternationalizationExtension(InternationalizationExtension):
    """
    We override jinja2's _parse_block() to collapse whitespace so we can have
    linebreaks wherever we want.
    """

    def _parse_block(self, parser, allow_pluralize):
        parse_block = InternationalizationExtension._parse_block
        ref, buffer = parse_block(self, parser, allow_pluralize)
        return ref, strip_whitespace(buffer)
