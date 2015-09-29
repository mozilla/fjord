import sys
from functools import wraps

import requests_mock
from mock import MagicMock, patch

from django.test.utils import override_settings

from fjord.base.google_utils import GOOGLE_API_URL, ga_track_event
from fjord.base.tests import TestCase


def set_sys_argv(sys_argv):
    """Decorator for setting sys.argv

    ::

        class SomeTestCase(TestCase):
            @set_sys_argv(['test'])
            def test_something(self):
                ...

    """
    def _set_sys_argv(fun):
        @wraps(fun)
        def handler(*args, **kwargs):
            _old_sys_argv = sys.argv
            sys.argv = sys_argv
            try:
                return fun(*args, **kwargs)
            finally:
                sys.argv = _old_sys_argv
        return handler
    return _set_sys_argv


class TestGoogleUtils(TestCase):
    @override_settings(DEBUG=True)
    @set_sys_argv([])
    def test_ga_track_event_debug_prefixes_with_test(self):
        with patch('fjord.base.google_utils.requests') as req_patch:
            # Create a mock that we can call .post() on and query what
            # it got params-wise. It doesn't matter what the return
            # is.
            req_patch.post = MagicMock()
            params = {'cid': 'xxx', 'ec': 'ou812'}

            ga_track_event(params)

            req_patch.post.assert_called_once_with(
                GOOGLE_API_URL,
                data={
                    'tid': 'UA-35433268-26',
                    'v': '1',
                    't': 'event',
                    'ec': 'test_ou812',  # "test_" is prepended.
                    'cid': 'xxx'
                }
            )

    @set_sys_argv([])
    def test_ga_track_event_non_test(self):
        with patch('fjord.base.google_utils.requests') as req_patch:
            # Create a mock that we can call .post() on and query what
            # it got params-wise. It doesn't matter what the return
            # is.
            req_patch.post = MagicMock()
            params = {'cid': 'xxx', 'ec': 'ou812'}

            ga_track_event(params)

            req_patch.post.assert_called_once_with(
                GOOGLE_API_URL,
                data={
                    'tid': 'UA-35433268-26',
                    'v': '1',
                    't': 'event',
                    'ec': 'ou812',  # "test_" is not prepended.
                    'cid': 'xxx'
                }
            )

    @set_sys_argv([])
    def test_ga_track_event_async_true(self):
        """async=True, then delay() gets called once"""
        with requests_mock.Mocker() as m:
            m.post(GOOGLE_API_URL, text='')

            post_event = 'fjord.base.google_utils.post_event'
            post_event_delay = 'fjord.base.google_utils.post_event.delay'
            with patch(post_event) as post_event_patch:
                with patch(post_event_delay) as post_event_delay_patch:
                    params = {'cid': 'xxx', 'ec': 'ou812'}
                    ga_track_event(params, async=True)
                    assert post_event_patch.call_count == 0
                    assert post_event_delay_patch.call_count == 1

    @set_sys_argv([])
    def test_ga_track_event_async_false(self):
        """async=False, then delay() never gets called"""
        with requests_mock.Mocker() as m:
            m.post(GOOGLE_API_URL, text='')

            post_event = 'fjord.base.google_utils.post_event'
            post_event_delay = 'fjord.base.google_utils.post_event.delay'
            with patch(post_event) as post_event_patch:
                with patch(post_event_delay) as post_event_delay_patch:
                    params = {'cid': 'xxx', 'ec': 'ou812'}
                    ga_track_event(params, async=False)
                    assert post_event_patch.call_count == 1
                    assert post_event_delay_patch.call_count == 0
