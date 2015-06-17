from django.utils.translation import ugettext, ungettext


def install_gettext():
    """Install gettext into the Jinja2 environment."""
    class Translation(object):
        # We pass this object to jinja so it can use django's gettext
        # implementation.
        ugettext = staticmethod(ugettext)
        ungettext = staticmethod(ungettext)

    import jingo
    jingo.env.install_gettext_translations(Translation)
