import jinja2
from jinja2.ext import InternationalizationExtension

from fjord.l10n.utils import collapse_whitespace


@jinja2.contextfunction
def _gettext_alias(context, text, *args, **kwargs):
    """Marks result of gettext as 'safe'"""
    return jinja2.Markup(
        context.resolve('gettext')(context, text, *args, **kwargs)
    )


class TowerI18nExtension(InternationalizationExtension):
    """Provides gettext and trans tags

    Extends Jinja2's ``InternationalizationExtension`` with three key
    differences:

    1. shortens the name to something easier to type
    2. overrides ``_parse_block`` to collapse whitespace in trans tags
       so msgids don't change when we change indentation in Jinja2
       templates
    3. fixes gettext function in Jinja2 templates so the output
       is always marked safe and HTML is not escaped

    """

    def __init__(self, environment):
        super(TowerI18nExtension, self).__init__(environment)
        environment.globals['_'] = _gettext_alias

    def _parse_block(self, parser, allow_pluralize):
        parse_block = InternationalizationExtension._parse_block
        ref, buffer = parse_block(self, parser, allow_pluralize)
        return ref, collapse_whitespace(buffer)
