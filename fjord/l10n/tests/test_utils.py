from fjord.l10n.utils import collapse_whitespace


def test_collapse_whitespace():
    data = [
        ('', ''),
        ('    ', ''),
        ('  \n\t\r\n   ', ''),
        ('foo', 'foo'),
        ('   foo   ', 'foo'),
        ('   foo\n    bar', 'foo bar')
    ]
    for text, expected in data:
        assert collapse_whitespace(text) == expected
