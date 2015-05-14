import datetime
import json
import urllib
from uuid import uuid4

from django.test.utils import override_settings

from nose.tools import eq_, ok_

from . import AlertFlavorFactory, AlertFactory, LinkFactory
from fjord.alerts.models import Alert, Link
from fjord.api_auth.tests import TokenFactory
from fjord.base.tests import reverse, TestCase, WHATEVER


class AlertsGetAPIAuthTest(TestCase):
    def test_missing_flavor(self):
        qs = {
            'flavors': 'fooflavor'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs)
        )

        eq_(resp.status_code, 404)
        eq_(json.loads(resp.content),
            {'detail': {'flavor': ['Flavor "fooflavor" does not exist.']}}
        )

        qs = {
            'flavors': 'fooflavor,barflavor'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs)
        )

        eq_(resp.status_code, 404)
        eq_(json.loads(resp.content),
            {'detail': {'flavor': ['Flavor "fooflavor" does not exist.']}}
        )

        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')

        qs = {
            'flavors': 'barflavor,' + flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs)
        )

        eq_(resp.status_code, 404)
        eq_(json.loads(resp.content),
            {'detail': {'flavor': ['Flavor "barflavor" does not exist.']}}
        )

    def test_missing_auth_token(self):
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs)
        )

        eq_(resp.status_code, 401)
        eq_(json.loads(resp.content),
            {'detail': 'Authentication credentials were not provided.'}
        )

    def test_missing_malformed_auth_token(self):
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION=''
        )

        eq_(resp.status_code, 401)
        eq_(json.loads(resp.content),
            {'detail': 'Authentication credentials were not provided.'}
        )

        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token'
        )

        eq_(resp.status_code, 401)
        eq_(json.loads(resp.content),
            {'detail': 'Invalid token header. No token provided.'}
        )

        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token token token'
        )

        eq_(resp.status_code, 401)
        eq_(json.loads(resp.content),
            {'detail': ('Invalid token header. Token string should not '
                        'contain spaces.')}
        )

    def test_not_permitted(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 403)
        eq_(json.loads(resp.content),
            {'detail': 'You do not have permission to perform this action.'}
        )

    def test_not_all_permitted(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor2 = AlertFlavorFactory(name='Bar', slug='barflavor')
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug + ',' + flavor2.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 403)
        eq_(json.loads(resp.content),
            {'detail': 'You do not have permission to perform this action.'}
        )

        # Reverse the order of flavors to make sure that also works
        qs = {
            'flavors': flavor2.slug + ',' + flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 403)
        eq_(json.loads(resp.content),
            {'detail': 'You do not have permission to perform this action.'}
        )

    def test_disabled_flavor(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(
            name='Foo', slug='fooflavor', enabled=False)
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {'detail': {'flavor': ['Flavor "fooflavor" is disabled.']}}
        )

    def test_fjord_authorization_token(self):
        """Verify auth will use Fjord-Authorization header if Authorization
        isn't there

        """
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_FJORD_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 200)
        eq_(json.loads(resp.content),
            {u'count': 0, u'total': 0, u'alerts': []})


class AlertsGetAPITest(TestCase):
    def test_bad_args(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        AlertFactory(summary=u'alert 1', flavor=flavor)

        qs = {
            'flavors': flavor.slug,
            'foo': 'bar'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {
                'detail': {
                    'non_field_errors': ['"foo" is not a valid argument.']
                }
            })

    def test_get_one_flavor(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        AlertFactory(summary=u'alert 1', flavor=flavor)
        AlertFactory(summary=u'alert 2', flavor=flavor)
        AlertFactory(summary=u'alert 3', flavor=flavor)

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 200)
        eq_(
            json.loads(resp.content),
            {
                u'count': 3,
                u'total': 3,
                u'alerts': [
                    {
                        u'id': WHATEVER,
                        u'summary': u'alert 1',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': []
                    }, {
                        u'id': WHATEVER,
                        u'summary': u'alert 2',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': []
                    }, {
                        u'id': WHATEVER,
                        u'summary': u'alert 3',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': []
                    }
                ]
            }
        )

    def test_get_multiple_flavors(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        flavor2 = AlertFlavorFactory(name='Bar', slug='barflavor')
        flavor2.allowed_tokens.add(token)

        AlertFactory(summary=u'alert 1', flavor=flavor)
        AlertFactory(summary=u'alert 2', flavor=flavor2)

        qs = {
            'flavors': flavor.slug + ',' + flavor2.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 200)
        eq_(
            json.loads(resp.content),
            {
                u'count': 2,
                u'total': 2,
                u'alerts': [
                    {
                        u'id': WHATEVER,
                        u'summary': u'alert 1',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': []
                    }, {
                        u'id': WHATEVER,
                        u'summary': u'alert 2',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor2.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': []
                    }
                ]
            }
        )

    def test_max(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        alert1 = AlertFactory(summary=u'alert 1', flavor=flavor)
        # We backdate the created so we can verify we're getting the
        # right order of alerts.
        alert1.created = datetime.datetime.now() - datetime.timedelta(days=5)
        alert1.save()

        AlertFactory(summary=u'alert 2', flavor=flavor)

        qs = {
            'flavors': flavor.slug,
            'max': 1
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 200)
        eq_(
            json.loads(resp.content),
            {
                u'count': 1,
                u'total': 2,
                u'alerts': [
                    {
                        u'id': WHATEVER,
                        u'summary': u'alert 2',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': []
                    }
                ]
            }
        )

    def test_bad_max(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug,
            'max': 'one'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {'detail': {'max': ['Enter a whole number.']}}
        )

        qs = {
            'flavors': flavor.slug,
            'max': 0
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {'detail': {'max': ['This field must be positive and non-zero.']}}
        )

    def test_start_time(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        daybeforeyesterday = yesterday - datetime.timedelta(days=1)

        alert1 = AlertFactory(
            summary=u'alert 1',
            flavor=flavor,
            start_time=yesterday
        )
        alert2 = AlertFactory(
            summary=u'alert 2',
            flavor=flavor,
            start_time=daybeforeyesterday
        )

        def test_scenario(start_time_start, start_time_end, expected):
            qs = {
                'flavors': flavor.slug,
            }
            if start_time_start:
                qs['start_time_start'] = start_time_start
            if start_time_end:
                qs['start_time_end'] = start_time_end

            resp = self.client.get(
                reverse('alerts-api') + '?' + urllib.urlencode(qs),
                HTTP_AUTHORIZATION='token ' + token.token
            )

            eq_(resp.status_code, 200)
            data = json.loads(resp.content)
            eq_(sorted([alert['summary'] for alert in data['alerts']]),
                sorted(expected))

        # Start yesterday at 00:00
        test_scenario(
            start_time_start=yesterday.strftime('%Y-%m-%dT00:00'),
            start_time_end=None,
            expected=[alert1.summary]
        )

        # Start today at 00:00
        test_scenario(
            start_time_start=today.strftime('%Y-%m-%dT00:00'),
            start_time_end=None,
            expected=[]
        )

        # End today at 23:59
        test_scenario(
            start_time_start=None,
            start_time_end=today.strftime('%Y-%m-%dT23:59'),
            expected=[alert1.summary, alert2.summary]
        )

        # End day before yesterday at 00:00
        test_scenario(
            start_time_start=None,
            start_time_end=daybeforeyesterday.strftime('%Y-%m-%dT23:59'),
            expected=[alert2.summary]
        )

        # Start daybeforeyesterday at 00:00 and end today at 23:59
        test_scenario(
            start_time_start=daybeforeyesterday.strftime('%Y-%m-%dT00:00'),
            start_time_end=today.strftime('%Y-%m-%dT23:59'),
            expected=[alert1.summary, alert2.summary]
        )

    def test_start_time_invalid(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug,
            'start_time_start': 'one',
            'start_time_end': 'one'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        data = json.loads(resp.content)
        ok_(data['detail']['start_time_start'][0]
            .startswith('Datetime has wrong format'))
        ok_(data['detail']['start_time_end'][0]
            .startswith('Datetime has wrong format'))

        qs = {
            'flavors': flavor.slug,
            'start_time_start': datetime.datetime.now(),
            'start_time_end': (
                datetime.datetime.now() - datetime.timedelta(days=1)
            )
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        data = json.loads(resp.content)
        eq_(data['detail'],
            {'non_field_errors': [
                u'start_time_start must occur before start_time_end.'
            ]}
        )

    def test_end_time(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        daybeforeyesterday = yesterday - datetime.timedelta(days=1)

        alert1 = AlertFactory(
            summary=u'alert 1',
            flavor=flavor,
            end_time=yesterday
        )
        alert2 = AlertFactory(
            summary=u'alert 2',
            flavor=flavor,
            end_time=daybeforeyesterday
        )

        def test_scenario(end_time_start, end_time_end, expected):
            qs = {
                'flavors': flavor.slug,
            }
            if end_time_start:
                qs['end_time_start'] = end_time_start
            if end_time_end:
                qs['end_time_end'] = end_time_end

            resp = self.client.get(
                reverse('alerts-api') + '?' + urllib.urlencode(qs),
                HTTP_AUTHORIZATION='token ' + token.token
            )

            eq_(resp.status_code, 200)
            data = json.loads(resp.content)
            eq_(sorted([alert['summary'] for alert in data['alerts']]),
                sorted(expected))

        # Start yesterday at 00:00
        test_scenario(
            end_time_start=yesterday.strftime('%Y-%m-%dT00:00'),
            end_time_end=None,
            expected=[alert1.summary]
        )

        # Start today at 00:00
        test_scenario(
            end_time_start=today.strftime('%Y-%m-%dT00:00'),
            end_time_end=None,
            expected=[]
        )

        # End today at 23:59
        test_scenario(
            end_time_start=None,
            end_time_end=today.strftime('%Y-%m-%dT23:59'),
            expected=[alert1.summary, alert2.summary]
        )

        # End day before yesterday at 00:00
        test_scenario(
            end_time_start=None,
            end_time_end=daybeforeyesterday.strftime('%Y-%m-%dT23:59'),
            expected=[alert2.summary]
        )

        # Start daybeforeyesterday at 00:00 and end today at 23:59
        test_scenario(
            end_time_start=daybeforeyesterday.strftime('%Y-%m-%dT00:00'),
            end_time_end=today.strftime('%Y-%m-%dT23:59'),
            expected=[alert1.summary, alert2.summary]
        )

    def test_end_time_invalid(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug,
            'end_time_start': 'one',
            'end_time_end': 'one'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        data = json.loads(resp.content)
        ok_(data['detail']['end_time_start'][0]
            .startswith('Datetime has wrong format'))
        ok_(data['detail']['end_time_end'][0]
            .startswith('Datetime has wrong format'))

        qs = {
            'flavors': flavor.slug,
            'end_time_start': datetime.datetime.now(),
            'end_time_end': (
                datetime.datetime.now() - datetime.timedelta(days=1)
            )
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        data = json.loads(resp.content)
        eq_(data['detail'],
            {'non_field_errors': [
                u'end_time_start must occur before end_time_end.'
            ]}
        )

    def test_created(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        daybeforeyesterday = yesterday - datetime.timedelta(days=1)

        alert1 = AlertFactory(summary=u'alert 1', flavor=flavor)
        alert1.created = yesterday
        alert1.save()

        alert2 = AlertFactory(summary=u'alert 2', flavor=flavor)
        alert2.created = daybeforeyesterday
        alert2.save()

        def test_scenario(created_start, created_end, expected):
            qs = {
                'flavors': flavor.slug,
            }
            if created_start:
                qs['created_start'] = created_start
            if created_end:
                qs['created_end'] = created_end

            resp = self.client.get(
                reverse('alerts-api') + '?' + urllib.urlencode(qs),
                HTTP_AUTHORIZATION='token ' + token.token
            )

            eq_(resp.status_code, 200)
            data = json.loads(resp.content)
            eq_(sorted([alert['summary'] for alert in data['alerts']]),
                sorted(expected))

        # Start yesterday at 00:00 yields alert1.
        test_scenario(
            created_start=yesterday.strftime('%Y-%m-%dT00:00'),
            created_end=None,
            expected=[alert1.summary]
        )

        # Start today at 00:00 yields nothing.
        test_scenario(
            created_start=today.strftime('%Y-%m-%dT00:00'),
            created_end=None,
            expected=[]
        )

        # End today at 23:59 yields both.
        test_scenario(
            created_start=None,
            created_end=today.strftime('%Y-%m-%dT23:59'),
            expected=[alert1.summary, alert2.summary]
        )

        # End day before yesterday at 00:00 yields alert2.
        test_scenario(
            created_start=None,
            created_end=daybeforeyesterday.strftime('%Y-%m-%dT23:59'),
            expected=[alert2.summary]
        )

        # Start daybeforeyesterday at 00:00 and end today at 23:59 yields
        # both.
        test_scenario(
            created_start=daybeforeyesterday.strftime('%Y-%m-%dT00:00'),
            created_end=today.strftime('%Y-%m-%dT23:59'),
            expected=[alert1.summary, alert2.summary]
        )

    def test_created_invalid(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        qs = {
            'flavors': flavor.slug,
            'created_start': 'one',
            'created_end': 'one'
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        data = json.loads(resp.content)
        ok_(data['detail']['created_start'][0]
            .startswith('Datetime has wrong format'))
        ok_(data['detail']['created_end'][0]
            .startswith('Datetime has wrong format'))

        qs = {
            'flavors': flavor.slug,
            'created_start': datetime.datetime.now(),
            'created_end': (
                datetime.datetime.now() - datetime.timedelta(days=1)
            )
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        data = json.loads(resp.content)
        eq_(data['detail'],
            {'non_field_errors': [
                u'created_start must occur before created_end.'
            ]}
        )

    def test_links(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        alert = AlertFactory(summary=u'alert 1', flavor=flavor)
        link = LinkFactory(alert=alert)

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 200)
        eq_(
            json.loads(resp.content),
            {
                u'count': 1,
                u'total': 1,
                u'alerts': [
                    {
                        u'id': WHATEVER,
                        u'summary': u'alert 1',
                        u'description': u'the account balance is at $5.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'balance-checker',
                        u'start_time': None,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 0,
                        u'links': [
                            {u'name': link.name, u'url': link.url}
                        ]
                    }
                ]
            }
        )


class AlertsPostAPITest(TestCase):
    def test_post(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        data = {
            'severity': 5,
            'summary': 'test alert',
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 201)
        alert = Alert.objects.latest('id')
        eq_(json.loads(resp.content), {'detail': {'id': alert.id}})
        eq_(alert.flavor.slug, flavor.slug)
        eq_(alert.severity, data['severity'])
        eq_(alert.summary, data['summary'])
        eq_(alert.emitter_name, data['emitter_name'])
        eq_(alert.emitter_version, data['emitter_version'])

    @override_settings(TIME_ZONE='America/Los_Angeles')
    def test_post_with_dates(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        data = {
            'severity': 5,
            'summary': 'test alert',
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'start_time': '2015-03-02T16:22:00Z',
            'end_time': '2015-03-02T17:23:00Z'
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 201)
        alert = Alert.objects.latest('id')
        eq_(json.loads(resp.content), {'detail': {'id': alert.id}})
        eq_(alert.start_time, datetime.datetime(2015, 3, 2, 8, 22, 0))
        eq_(alert.end_time, datetime.datetime(2015, 3, 2, 9, 23, 0))

    def test_post_invalid_start_time(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        data = {
            'severity': 5,
            'summary': 'test alert',
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'start_time': '2015'
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )
        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {
                u'detail': {
                    u'start_time': [
                        u'Datetime has wrong format. Use one of these formats '
                        u'instead: '
                        u'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]'
                    ]
                }
            }
        )

    @override_settings(TIME_ZONE='America/Los_Angeles')
    def test_post_start_time_timezone_change(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        data = {
            'severity': 5,
            'summary': 'test alert',
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'start_time': '2015-03-02T16:22:00-0600',
            'end_time': '2015-03-02T17:23:00-0600'
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 201)
        alert = Alert.objects.latest('id')
        eq_(json.loads(resp.content), {'detail': {'id': alert.id}})
        eq_(alert.start_time, datetime.datetime(2015, 3, 2, 14, 22, 0))
        eq_(alert.end_time, datetime.datetime(2015, 3, 2, 15, 23, 0))

    @override_settings(TIME_ZONE='America/Los_Angeles')
    def test_post_date_roundtrip(self):
        """Test we can POST a date and then GET the same date back"""
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        start_time = '2015-03-02T16:22:00Z'

        data = {
            'severity': 5,
            'summary': 'test alert',
            'description': (
                'One if by land.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'start_time': start_time
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 201)
        alert = Alert.objects.latest('id')
        eq_(json.loads(resp.content), {'detail': {'id': alert.id}})
        eq_(alert.start_time, datetime.datetime(2015, 3, 2, 8, 22, 0))

        qs = {
            'flavors': flavor.slug
        }
        resp = self.client.get(
            reverse('alerts-api') + '?' + urllib.urlencode(qs),
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 200)
        eq_(
            json.loads(resp.content),
            {
                u'count': 1,
                u'total': 1,
                u'alerts': [
                    {
                        u'id': WHATEVER,
                        u'summary': u'test alert',
                        u'description': u'One if by land.',
                        u'flavor': flavor.slug,
                        u'emitter_version': 0,
                        u'emitter_name': u'testemitter',
                        u'start_time': start_time,
                        u'end_time': None,
                        u'created': WHATEVER,
                        u'severity': 5,
                        u'links': [],
                    }
                ]
            }
        )

    def test_post_with_link(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        data = {
            'severity': 5,
            'summary': 'test alert',
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'links': [{'name': 'link', 'url': 'http://example.com/'}]
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 201)
        alert = Alert.objects.latest('id')
        eq_(json.loads(resp.content), {'detail': {'id': alert.id}})

        links = Link.objects.filter(alert=alert)
        eq_(len(links), 1)
        eq_(links[0].name, 'link')
        eq_(links[0].url, 'http://example.com/')

    def test_invalid_links(self):
        token = TokenFactory()
        flavor = AlertFlavorFactory(name='Foo', slug='fooflavor')
        flavor.allowed_tokens.add(token)

        # Missing link name
        data = {
            'severity': 5,
            'summary': str(uuid4()),
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'links': [{'url': 'http://example.com/'}]
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {
                u'detail': {
                    'links': (
                        'Missing names or urls in link data. '
                        "[{u'url': u'http://example.com/'}]"
                    )
                }
            }
        )
        eq_(Alert.objects.filter(summary=data['summary']).count(), 0)

        # Missing link url
        data = {
            'severity': 5,
            'summary': str(uuid4()),
            'description': (
                'All we ever see of stars are their old photographs.'
            ),
            'flavor': flavor.slug,
            'emitter_name': 'testemitter',
            'emitter_version': 0,
            'links': [{'name': 'link'}]
        }

        resp = self.client.post(
            reverse('alerts-api'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='token ' + token.token
        )

        eq_(resp.status_code, 400)
        eq_(json.loads(resp.content),
            {
                u'detail': {
                    'links': (
                        'Missing names or urls in link data. '
                        "[{u'name': u'link'}]"
                    )
                }
            }
        )
        eq_(Alert.objects.filter(summary=data['summary']).count(), 0)
