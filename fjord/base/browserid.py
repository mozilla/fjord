import urlparse

from django.http import HttpResponseRedirect

from django_browserid.views import Verify

from fjord.base.models import Profile
from fjord.base.urlresolvers import reverse


class FjordVerify(Verify):
    def login_success(self):
        """Send to new-user-view if new user, otherwise send on their way"""
        response = super(FjordVerify, self).login_success()
        # If this user has never logged in before, send them to our
        # super secret "Welcome!" page.
        try:
            self.user.profile
            return response

        except Profile.DoesNotExist:
            url = reverse('new-user-view')

            redirect_to = self.request.REQUEST.get('next')

            # Do not accept redirect URLs pointing to a different host.
            if redirect_to:
                netloc = urlparse.urlparse(redirect_to).netloc
                if netloc and netloc != self.request.get_host():
                    redirect_to = None

            if redirect_to:
                url = url + '?next=' + redirect_to

            return HttpResponseRedirect(url)
