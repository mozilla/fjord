from datetime import date, timedelta

from django.views.decorators.csrf import csrf_exempt

import rest_framework.generics
import rest_framework.views
import rest_framework.response

from elasticsearch_dsl import F

from fjord.analytics.utils import zero_fill
from fjord.base.utils import (
    actual_ip_plus_context,
    cors_enabled,
    RatelimitThrottle,
    smart_date,
    smart_int,
    smart_timedelta
)
from fjord.feedback import models


class FeedbackHistogramAPI(rest_framework.views.APIView):
    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(FeedbackHistogramAPI, cls).as_view(*args, **kwargs)
        view = cors_enabled('*', methods=['GET'])(view)
        return view

    def get(self, request):
        # FIXME: Rewrite this to use aggs and allow multiple layers.
        search = models.ResponseDocType.docs.search()
        f = F()

        if 'happy' in request.GET:
            happy = {'0': False, '1': True}.get(request.GET['happy'], None)
            if happy is not None:
                f &= F('term', happy=happy)

        if 'platforms' in request.GET:
            platforms = request.GET['platforms'].split(',')
            if platforms:
                f &= F('terms', platform=platforms)

        if 'locales' in request.GET:
            locales = request.GET['locales'].split(',')
            if locales:
                f &= F('terms', locale=locales)

        if 'products' in request.GET:
            products = request.GET['products'].split(',')
            if products:
                f &= F('terms', product=products)

                if 'versions' in request.GET:
                    versions = request.GET['versions'].split(',')
                    if versions:
                        f &= F('terms', version=versions)

        if 'source' in request.GET:
            # FIXME: Having a , in the source is valid, so this might not work
            # right.
            sources = request.GET['source'].split(',')
            if sources:
                f &= F('terms', source=sources)

        if 'api' in request.GET:
            # The int (as a str) or "None"
            apis = request.GET['api'].split(',')
            if apis:
                f &= F('terms', api=apis)

        date_start = smart_date(request.GET.get('date_start', None))
        date_end = smart_date(request.GET.get('date_end', None))
        delta = smart_timedelta(request.GET.get('date_delta', None))

        # Default to 7d.
        if not date_start and not date_end:
            delta = delta or smart_timedelta('7d')

        if delta is not None:
            if date_end is not None:
                date_start = date_end - delta
            elif date_start is not None:
                date_end = date_start + delta
            else:
                date_end = date.today()
                date_start = date_end - delta

        # If there's no end, then the end is today.
        if not date_end:
            date_end = date.today()

        # Restrict to a 6 month range. Must have a start date.
        if (date_end - date_start) > timedelta(days=180):
            date_end = date_start + timedelta(days=180)

        # date_start up to but not including date_end.
        f &= F('range', created={'gte': date_start, 'lt': date_end})

        search_query = request.GET.get('q', None)
        if search_query is not None:
            search = search.query(
                'simple_query_string', query=search_query,
                fields=['description'])

        search = search.filter(f)

        # FIXME: improve validation
        interval = request.GET.get('interval', 'day')
        if interval not in ('hour', 'day'):
            interval = 'day'

        search.aggs.bucket(
            'histogram',
            'date_histogram',
            field='created',
            interval=interval
        )

        resp = search.execute()

        data = dict((p['key'], p['doc_count'])
                    for p in resp.aggregations['histogram']['buckets'])
        zero_fill(date_start, date_end - timedelta(days=1), [data])

        return rest_framework.response.Response({
            'results': sorted(data.items())
        })

    def get_throttles(self):
        """Returns throttle class instances"""
        return [
            RatelimitThrottle(
                rulename='api_get_2000ph',
                rate='2000/h',
                methods=('GET',))
        ]


class PublicFeedbackAPI(rest_framework.views.APIView):
    def get(self, request):
        """Returns JSON feed of first 10000 results

        This feels like a duplication of the front-page dashboard search
        logic, but it's separate which allows us to handle multiple
        values.

        """
        search = models.ResponseDocType.docs.search()
        f = F()

        if 'id' in request.GET:
            id_list = request.GET['id'].split(',')
            id_list = [smart_int(id_, fallback=None) for id_ in id_list]
            id_list = [id_ for id_ in id_list if id_]

            f &= F('terms', id=id_list)

        else:
            if 'happy' in request.GET:
                happy = {'0': False, '1': True}.get(request.GET['happy'], None)
                if happy is not None:
                    f &= F('term', happy=happy)

            if 'platforms' in request.GET:
                platforms = request.GET['platforms'].split(',')
                if platforms:
                    f &= F('terms', platform=platforms)

            if 'locales' in request.GET:
                locales = request.GET['locales'].split(',')
                if locales:
                    f &= F('terms', locale=locales)

            if 'products' in request.GET:
                products = request.GET['products'].split(',')
                if products:
                    f &= F('terms', product=products)

                    if 'versions' in request.GET:
                        versions = request.GET['versions'].split(',')
                        if versions:
                            f &= F('terms', version=versions)

            date_start = smart_date(request.GET.get('date_start', None))
            date_end = smart_date(request.GET.get('date_end', None))
            delta = smart_timedelta(request.GET.get('date_delta', None))

            if delta is not None:
                if date_end is not None:
                    date_start = date_end - delta
                elif date_start is not None:
                    date_end = date_start + delta
                else:
                    date_end = date.today()
                    date_start = date_end - delta

            # We restrict public API access to the last 6 months.
            six_months_ago = date.today() - timedelta(days=180)
            if date_start:
                date_start = max(six_months_ago, date_start)
                f &= F('range', created={'gte': date_start})
            if date_end:
                date_end = max(six_months_ago, date_end)
                f &= F('range', created={'lte': date_end})

            search_query = request.GET.get('q', None)
            if search_query is not None:
                search = search.query('simple_query_string',
                                      query=search_query,
                                      fields=['description'])

            # FIXME: Probably want to make this specifyable
            search = search.sort('-created')

        search = search.filter(f)

        maximum = smart_int(request.GET.get('max', None))
        maximum = maximum or 1000
        maximum = min(max(1, maximum), 10000)

        responses = list(search[:maximum].execute())
        responses = models.ResponseDocType.docs.to_public(responses)

        return rest_framework.response.Response({
            'count': len(responses),
            'results': responses
        })

    def get_throttles(self):
        """Returns throttle class instances"""
        return [
            RatelimitThrottle(
                rulename='api_get_200ph',
                rate='200/h',
                methods=('GET',))
        ]


PER_HOUR_LIMIT = 50


class PostFeedbackAPI(rest_framework.generics.CreateAPIView):
    serializer_class = models.PostResponseSerializer

    def get_throttles(self):
        """Returns throttle class instances"""
        def _get_desc(req):
            return req.data.get('description', u'no description')

        return [
            RatelimitThrottle(
                rulename='api_post_{n}ph'.format(n=PER_HOUR_LIMIT),
                rate='{n}/h'.format(n=PER_HOUR_LIMIT)),
            RatelimitThrottle(
                rulename='api_post_doublesubmit_1p10m',
                rate='1/10m',
                keyfun=actual_ip_plus_context(_get_desc))
        ]


def feedback_as_view():
    """Manual method routing so we can throttle in different ways"""
    public_feedback_api_view = PublicFeedbackAPI.as_view()
    post_feedback_api_view = PostFeedbackAPI.as_view()

    @csrf_exempt
    @cors_enabled('*', methods=['GET', 'POST'])
    def _feedback_api_router(request):
        if request.method == 'POST':
            return post_feedback_api_view(request)
        else:
            return public_feedback_api_view(request)
    return _feedback_api_router
