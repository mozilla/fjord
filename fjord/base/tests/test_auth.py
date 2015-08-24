import json

from django.test.client import RequestFactory

from fjord.base.browserid import FjordVerify
from fjord.base.tests import (
    BaseTestCase,
    ProfileFactory,
    reverse,
    UserFactory
)


class TestAuth(BaseTestCase):
    def test_new_user(self):
        """Tests that new users get redirected to new_user page"""
        # Create a user that has no profile--this is the sign that the
        # user is new!
        new_user = UserFactory(profile=None)
        self.client_login_user(new_user)

        # Now do some ridiculous setup so we can call login_success()
        # on the Verify and see if it did what it should be doing.

        # FIXME - this can go away post django-browserid 0.9
        new_user.backend = 'django_browserid.auth.BrowserIDBackend'

        post_request = RequestFactory().post(reverse('browserid.login'))
        post_request.user = new_user
        post_request.session = self.client.session

        fv = FjordVerify()
        fv.user = new_user
        fv.request = post_request

        resp = fv.login_success()
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert body['redirect'] == reverse('new-user-view')

    def test_existing_user(self):
        """Tests that existing users get redirected to right place"""
        new_user = ProfileFactory().user
        self.client_login_user(new_user)

        # Now do some ridiculous setup so we can call login_success()
        # on the Verify and see if it did what it should be doing.

        # FIXME - this can go away post django-browserid 0.9
        new_user.backend = 'django_browserid.auth.BrowserIDBackend'

        # First, do it RAW!
        post_request = RequestFactory().post(reverse('browserid.login'))
        post_request.user = new_user
        post_request.session = self.client.session

        fv = FjordVerify()
        fv.user = new_user
        fv.request = post_request

        resp = fv.login_success()
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert body['redirect'] == '/'

        # Now do it with next!
        post_request = RequestFactory().post(
            reverse('browserid.login'),
            {'next': '/foo'})
        post_request.user = new_user
        post_request.session = self.client.session

        fv = FjordVerify()
        fv.user = new_user
        fv.request = post_request

        resp = fv.login_success()
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert body['redirect'] == '/foo'
