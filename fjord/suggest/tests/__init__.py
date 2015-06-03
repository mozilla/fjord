from django.test import RequestFactory

from fjord.base.plugin_utils import load_providers
from fjord.base.tests import reverse
from fjord.suggest import _SUGGESTERS


class SuggesterTestMixin(object):
    """Mixin that loads Suggesters specified with ``suggesters`` attribute"""
    suggesters = []

    def setUp(self):
        self.factory = RequestFactory()
        _SUGGESTERS[:] = load_providers(self.suggesters)
        super(SuggesterTestMixin, self).setUp()

    def tearDown(self):
        _SUGGESTERS[:] = []
        super(SuggesterTestMixin, self).tearDown()

    def get_feedback_post_request(self, params):
        url = reverse('feedback', args=(u'firefox',))
        return self.factory.post(url, params)
