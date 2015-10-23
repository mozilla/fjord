from jinja2 import contextfunction, DictLoader, Environment
from jinja2.utils import Markup


languages = {
    'xx': {
        'tower rules!': 'TOWER RULES!',
        'Tower rules!': 'TOWER RULES!',
        '%(count)s tower rules!': '%(count)s TOWER RULES!',
        '%(count)s towers rule!': '%(count)s TOWERS RULE!',
        'blue towers rule!': 'BLUE TOWERS RULE!',
        '<b>blue towers rule!</b>': '<b>BLUE TOWERS RULE!</b>',
    }
}


@contextfunction
def gettext(context, msgid):
    language = context.get('LANGUAGE', 'en')
    rv = languages.get(language, {}).get(msgid, msgid)
    if context.eval_ctx.autoescape:
        rv = Markup(rv)
    return rv


@contextfunction
def ngettext(context, msgid, msgid_plural, n):
    language = context.get('LANGUAGE', 'en')
    if n != 1:
        rv = languages.get(language, {}).get(msgid_plural, msgid_plural)
    else:
        rv = languages.get(language, {}).get(msgid, msgid)
    if context.eval_ctx.autoescape:
        rv = Markup(rv)
    return rv


def build_environment(template):
    env = Environment(
        # undefined=Undefined,
        autoescape=True,
        loader=DictLoader({'tmpl.html': template}),
        extensions=[
            'fjord.l10n.ext.TowerI18nExtension'
        ]
    )
    env.install_gettext_callables(gettext, ngettext, newstyle=True)
    return env


def render(template, *args, **kwargs):
    env = build_environment(template)
    return env.from_string(template).render(*args, **kwargs)


class TestTowerI18nExtension:
    def test_gettext(self):
        """gettext works"""
        tmpl = '{{ _("blue towers rule!") }}'
        assert render(tmpl, LANGUAGE='en') == 'blue towers rule!'
        assert render(tmpl, LANGUAGE='xx') == 'BLUE TOWERS RULE!'

    def test_gettext_is_safe(self):
        """html in gettext is safe"""
        tmpl = '{{ _("<b>blue towers rule!</b>") }}'
        assert render(tmpl, LANGUAGE='en') == '<b>blue towers rule!</b>'
        assert render(tmpl, LANGUAGE='xx') == '<b>BLUE TOWERS RULE!</b>'

    def test_gettext_notsafe(self):
        """interpolated html is not safe"""
        tmpl = '{{ _("<b>%(foo)s</b>", foo="<p>") }}'
        assert render(tmpl, LANGUAGE='en') == '<b>&lt;p&gt;</b>'

    def test_gettext_format_notsafe(self):
        """format html is not safe"""
        tmpl = '{{ _("<b>{0}</b>").format("<p>") }}'
        assert render(tmpl, LANGUAGE='en') == '<b>&lt;p&gt;</b>'

    def test_trans(self):
        tmpl = '<div>{% trans %}tower rules!{% endtrans %}</div>'
        assert render(tmpl, LANGUAGE='en') == '<div>tower rules!</div>'
        assert render(tmpl, LANGUAGE='xx') == '<div>TOWER RULES!</div>'

    def test_trans_whitespace(self):
        tmpl = (
            '<div>\n'
            '  {% trans %}\n'
            '    Tower\n'
            '    rules!\n'
            '  {% endtrans %}\n'
            '</div>\n'
        )
        assert (
            render(tmpl, LANGUAGE='en') ==
            (
                '<div>\n'
                '  Tower rules!\n'
                '</div>'
            )
        )
        assert (
            render(tmpl, LANGUAGE='xx') ==
            (
                '<div>\n'
                '  TOWER RULES!\n'
                '</div>'
            )
        )

    def test_trans_plural(self):
        tmpl = (
            '<div>\n'
            '  {% trans count %}\n'
            '    {{ count }} tower rules!\n'
            '  {% pluralize %}\n'
            '    {{ count }} towers rule!\n'
            '  {% endtrans %}\n'
            '</div>'
        )
        assert (
            render(tmpl, count=1, LANGUAGE='en') ==
            (
                '<div>\n'
                '  1 tower rules!\n'
                '</div>'
            )
        )
        assert (
            render(tmpl, count=2, LANGUAGE='en') ==
            (
                '<div>\n'
                '  2 towers rule!\n'
                '</div>'
            )
        )
        assert (
            render(tmpl, count=1, LANGUAGE='xx') ==
            (
                '<div>\n'
                '  1 TOWER RULES!\n'
                '</div>'
            )
        )
        assert (
            render(tmpl, count=2, LANGUAGE='xx') ==
            (
                '<div>\n'
                '  2 TOWERS RULE!\n'
                '</div>'
            )
        )

    def test_trans_interpolation(self):
        tmpl = (
            '{% trans tag="<p>" %}\n'
            '  this is a tag <b>{{ tag }}</b>\n'
            '{% endtrans %}'
        )
        assert (
            render(tmpl, LANGUAGE='en') ==
            'this is a tag <b>&lt;p&gt;</b>'
        )
