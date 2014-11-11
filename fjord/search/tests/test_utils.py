from nose.tools import eq_

from fjord.search.utils import from_class_path, to_class_path


class FooBarClassOfAwesome(object):
    pass


def test_from_class_path():
    eq_(
        from_class_path(
            'fjord.search.tests.test_utils:FooBarClassOfAwesome'),
        FooBarClassOfAwesome
    )


def test_to_class_path():
    eq_(
        to_class_path(FooBarClassOfAwesome),
        'fjord.search.tests.test_utils:FooBarClassOfAwesome'
    )
