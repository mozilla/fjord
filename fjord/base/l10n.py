# NOTE: The code in this file was mostly copied from tower.
import inspect
import re

import jinja2
from jinja2.ext import InternationalizationExtension


def add_context(context, message):
    # \x04 is a magic gettext number.
    return u'%s\x04%s' % (context, message)


def split_context(message):
    # \x04 is a magic gettext number.
    ret = message.split(u'\x04')
    if len(ret) == 1:
        ret.insert(0, '')
    return ret


def collapse_whitespace(message):
    return re.compile(r'\s+', re.UNICODE).sub(' ', message).strip()


@jinja2.contextfunction
def _gettext_alias(context, text, *args, **kwargs):
    """Takes the result of gettext and marks it safe"""
    return jinja2.Markup(
        context.resolve('gettext')(context, text, *args, **kwargs)
    )


class MozInternationalizationExtension(InternationalizationExtension):
    """
    We override jinja2's _parse_block() to collapse whitespace so we can have
    linebreaks wherever we want, and hijack _() to mark the result as safe.
    """

    def __init__(self, environment):
        super(MozInternationalizationExtension, self).__init__(environment)
        environment.globals['_'] = _gettext_alias

    def _yolo_is_trimmed(self):
        """Was the trans block marked "trimmed"

        NB: We don't have the information we need passed to us, so we have to
        inspect the stack. Yay.

        """
        frames = inspect.stack()
        # frame 0 is the current frame
        # frame 1 is _parse_block
        # frame 2 is the caller for _parse_block which has variables in it
        interesting_frame = frames[2][0]

        # If there's a local named "variables" and "trimmed" is in there,
        # then this trans block was marked with "trimmed"
        return 'trimmed' in interesting_frame.f_locals.get('variables', {})

    def _parse_block(self, parser, allow_pluralize):
        """parses the trans block

        This overrides trans parsing to look for a "trimmed" variable. If
        it's there, then this works just like Django's blocktrans and it'll
        collapse the whitespace in the trans tag.

        For example, this is not collapsed::

            {% trans %} ... {% endtrans %}

        This is collapsed::

            {% trans trimmed %} ... {% endtrans %}

        And this is also collapsed::

            {% trans foo=bar, trimmed %} ... {% endtrans %}

        """
        parse_block = InternationalizationExtension._parse_block
        ref, buffer = parse_block(self, parser, allow_pluralize)

        if self._yolo_is_trimmed():
            buffer = collapse_whitespace(buffer)
        return ref, buffer
