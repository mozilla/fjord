import logging
import urllib

from fjord.base.google_utils import ga_track_event
from fjord.feedback.models import Response as FeedbackResponse
from fjord.redirector import (
    Redirector,
    RedirectParseError,
    build_redirect_url
)
from fjord.suggest import Link, Suggester
from fjord.suggest.providers.trigger.models import TriggerRule


PROVIDER = 'trigger'
PROVIDER_VERSION = 1

TRIGGER = 'tgr'
EVENT_CATEGORY = 'trigger' + str(PROVIDER_VERSION)
SESSION_KEY = 'trigger_{0}'


logger = logging.getLogger('i.trigger')


def format_redirect(slug):
    return '{0}.{1}'.format(TRIGGER, slug)


def parse_redirect(redirect):
    try:
        trigger, slug = redirect.split('.')
        return trigger, slug
    except IndexError as exc:
        raise RedirectParseError(str(exc))


def build_ga_category(rule):
    return 'trigger_{rule.slug}_{rule.id}'.format(rule=rule)


def interpolate_url(url, response):
    if '{' not in url:
        return url

    data = {
        'LOCALE': urllib.quote_plus(response.locale.encode('utf-8')),
        'PRODUCT': urllib.quote_plus(response.product.encode('utf-8')),
        'VERSION': urllib.quote_plus(response.version.encode('utf-8')),
        'PLATFORM': urllib.quote_plus(response.platform.encode('utf-8')),
        'HAPPY': 'happy' if response.happy else 'sad',
    }
    return url.format(**data)


class TriggerRedirector(Redirector):
    """Provides redirection urls"""
    def handle_redirect(self, request, redirect):
        # If it's not a trigger redirect, return.
        if not redirect.startswith(TRIGGER):
            return

        # Get the response id for the last feedback left.
        response_id = request.session.get('response_id', None)
        if response_id is None:
            return

        # Extract the slug.
        try:
            trigger, slug = parse_redirect(redirect)
        except RedirectParseError:
            return

        # Get the rule that has that slug.
        try:
            rule = TriggerRule.objects.get(slug=slug)
        except TriggerRule.DoesNotExist:
            return

        # Interpolate the url.
        destination_url = rule.url
        if '{' in destination_url:
            # Fetch the response so we can interpolate the url.
            try:
                response = FeedbackResponse.objects.get(id=response_id)
            except FeedbackResponse.DoesNotExist:
                return
            destination_url = interpolate_url(destination_url, response)

        # Track the event and then return the new url.
        ga_track_event({
            'cid': str(response_id),
            'ec': build_ga_category(rule),
            'ea': 'view',
            'el': destination_url,
        }, async=True)

        return destination_url


class TriggerSuggester(Suggester):
    """Provides suggestions based on properties of the feedback"""
    def get_suggestions(self, feedback, request=None):
        # Note: This implementation assumes there aren't a fajillion
        # active rules. If that becomes a problem, we should
        # re-architect the db so that this is easier to implement.
        #
        # Further, each matching rule will kick off a GA event
        # request. We have to do those synchronously so that we're
        # guaranteed to have the "suggest" event before the "click"
        # event. Otherwise the data is not as meaningful.

        rules = TriggerRule.objects.all_enabled()
        links = []

        # Go through the rules and accrue links until we're done.
        # FIXME: Can we do one ga_track_event call for all the rules?
        for rule in rules:
            if rule.get_matcher().match(feedback):
                links.append(
                    Link(
                        provider=PROVIDER,
                        provider_version=PROVIDER_VERSION,
                        cssclass=u'document',
                        summary=rule.title,
                        description=rule.description,
                        url=build_redirect_url(format_redirect(rule.slug))
                    )
                )

                # Track category: trigger-slug, action: suggest
                ga_track_event({
                    'cid': str(feedback.id),
                    'ec': build_ga_category(rule),
                    'ea': 'suggest',
                    'el': rule.url
                })
        return links
