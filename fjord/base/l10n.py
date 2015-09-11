# NOTE: The code in this file was mostly copied from tower.
import re

# FIXME
# from django.utils.translation import ugettext, ungettext

import jinja2
from babel.messages.extract import extract_python as babel_extract_python
from jinja2 import ext
from jinja2.ext import InternationalizationExtension


# FIXME
# def install_gettext():
#     """Install gettext into the Jinja2 environment."""
#     class Translation(object):
#         # We pass this object to jinja so it can use django's gettext
#         # implementation.
#         ugettext = staticmethod(ugettext)
#         ungettext = staticmethod(ungettext)

#     import jingo
#     jingo.env.install_gettext_translations(Translation)


def add_context(context, message):
    # \x04 is a magic gettext number.
    return u'%s\x04%s' % (context, message)


def split_context(message):
    # \x04 is a magic gettext number.
    ret = message.split(u'\x04')
    if len(ret) == 1:
        ret.insert(0, '')
    return ret


def strip_whitespace(message):
    return re.compile(r'\s+', re.UNICODE).sub(' ', message).strip()


@jinja2.contextfunction
def _gettext_alias(context, text, *args, **kwargs):
    """Takes the result of gettext and marks it safe."""
    return jinja2.Markup(
        context.resolve('gettext')(text, *args, **kwargs)
    )


class MozInternationalizationExtension(InternationalizationExtension):
    """
    We override jinja2's _parse_block() to collapse whitespace so we can have
    linebreaks wherever we want, and hijack _() to mark the result as safe.
    """

    def __init__(self, environment):
        super(MozInternationalizationExtension, self).__init__(environment)
        environment.globals['_'] = _gettext_alias

    def _parse_block(self, parser, allow_pluralize):
        parse_block = InternationalizationExtension._parse_block
        ref, buffer = parse_block(self, parser, allow_pluralize)
        return ref, strip_whitespace(buffer)


def tweak_message(message):
    """We piggyback on jinja2's babel_extract() (really, Babel's extract_*
    functions) but they don't support some things we need so this function will
    tweak the message.  Specifically:

    1. We collapse whitespace in the msgid. Jinja2 will only strip
       whitespace from the ends of a string so linebreaks show up in
       your .po files still.

    2. Babel doesn't support context (msgctxt). We hack that in ourselves
       here.

    """
    if isinstance(message, basestring):
        message = strip_whitespace(message)

    elif isinstance(message, tuple):
        # A tuple of 2 has context, 3 is plural, 4 is plural with context
        if len(message) == 2:
            message = add_context(message[1], message[0])
        elif len(message) == 3:
            if all(isinstance(x, basestring) for x in message[:2]):
                singular, plural, num = message
                message = (strip_whitespace(singular),
                           strip_whitespace(plural),
                           num)
        elif len(message) == 4:
            singular, plural, num, ctxt = message
            message = (add_context(ctxt, strip_whitespace(singular)),
                       add_context(ctxt, strip_whitespace(plural)),
                       num)
    return message


def extract_python(fileobj, keywords, comment_tags, options):
    msgs = list(babel_extract_python(fileobj, keywords, comment_tags, options))
    for lineno, funcname, message, comments in msgs:
        message = tweak_message(message)
        yield lineno, funcname, message, comments


def extract_template(fileobj, keywords, comment_tags, options):
    msgs = list(ext.babel_extract(fileobj, keywords, comment_tags, options))
    for lineno, funcname, message, comments in msgs:
        message = tweak_message(message)
        yield lineno, funcname, message, comments
