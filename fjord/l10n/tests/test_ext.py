from jinja2 import DictLoader, contextfunction, Environment


templates = {
    'trans.html': (
        '<div>{% trans %}tower rules!{% endtrans %}</div>'
    ),
    'trans_whitespace.html': (
        '<div>\n'
        '  {% trans %}\n'
        '    Tower rules!\n'
        '    Yessiree!\n'
        '  {% endtrans %}\n'
        '</div>\n'
    ),
    'trans_plural.html': (
        '<div>\n'
        '  {% trans count %}\n'
        '    {{ count }} tower rules!\n'
        '  {% pluralize %}\n'
        '    {{ count }} towers rule!\n'
        '  {% endtrans %}\n'
        '</div>'
    ),
    'gettext.html': (
        '{{ _("blue towers rule!") }}'
    ),
    'gettext_safe.html': (
        '{{ _("<b>blue towers rule!</b>") }}'
    )
}


languages = {
    # NB: Translated into Pirate using Dennis.
    'xx': {
        'tower rules!': 'towerr rules arr!',
        'Tower rules! Yessiree!': 'Towerr rules! Yessiree shiver me timbers!',
        '%(count)s tower rules!': '%(count)s towerr rules arr!',
        '%(count)s towers rule!': '%(count)s towarrs rule arr!',
        'blue towers rule!': 'blue towarrs rule arr!',
        '<b>blue towers rule!</b>': '<b>blue towarrs rule arr!</b>',
    }
}


@contextfunction
def gettext(context, msgid):
    language = context.get('LANGUAGE', 'en')
    return languages.get(language, {}).get(msgid, msgid)


@contextfunction
def ngettext(context, msgid, msgid_plural, n):
    language = context.get('LANGUAGE', 'en')
    if n != 1:
        return languages.get(language, {}).get(msgid_plural, msgid_plural)
    return languages.get(language, {}).get(msgid, msgid)


i18n_env = Environment(
    loader=DictLoader(templates),
    extensions=['fjord.l10n.ext.TowerI18nExtension']
)
i18n_env.globals.update({
    '_':            gettext,
    'gettext':      gettext,
    'ngettext':     ngettext
})


class TestTowerI18nExtension:
    def test_gettext(self):
        tmpl = i18n_env.get_template('gettext.html')
        assert tmpl.render(LANGUAGE='en') == 'blue towers rule!'
        assert tmpl.render(LANGUAGE='xx') == 'blue towarrs rule arr!'

    def test_gettext_is_safe(self):
        tmpl = i18n_env.get_template('gettext_safe.html')
        assert tmpl.render(LANGUAGE='en') == '<b>blue towers rule!</b>'
        assert tmpl.render(LANGUAGE='xx') == '<b>blue towarrs rule arr!</b>'

    def test_trans(self):
        tmpl = i18n_env.get_template('trans.html')
        assert tmpl.render(LANGUAGE='en') == '<div>tower rules!</div>'
        assert tmpl.render(LANGUAGE='xx') == '<div>towerr rules arr!</div>'

    def test_trans_whitespace(self):
        tmpl = i18n_env.get_template('trans_whitespace.html')
        assert (
            tmpl.render(LANGUAGE='en') ==
            (
                '<div>\n'
                '  Tower rules! Yessiree!\n'
                '</div>'
            )
        )
        assert (
            tmpl.render(LANGUAGE='xx') ==
            (
                '<div>\n'
                '  Towerr rules! Yessiree shiver me timbers!\n'
                '</div>'
            )
        )

    def test_trans_plural(self):
        tmpl = i18n_env.get_template('trans_plural.html')
        assert (
            tmpl.render(LANGUAGE='en', count=1) ==
            (
                '<div>\n'
                '  1 tower rules!\n'
                '</div>'
            )
        )
        assert (
            tmpl.render(LANGUAGE='en', count=2) ==
            (
                '<div>\n'
                '  2 towers rule!\n'
                '</div>'
            )
        )
        assert (
            tmpl.render(LANGUAGE='xx', count=1) ==
            (
                '<div>\n'
                '  1 towerr rules arr!\n'
                '</div>'
            )
        )
        assert (
            tmpl.render(LANGUAGE='xx', count=2) ==
            (
                '<div>\n'
                '  2 towarrs rule arr!\n'
                '</div>'
            )
        )
