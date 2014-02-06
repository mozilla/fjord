# Note: These views are viewable only by people in the analyzers
# group. They should all have the analyzer_required decorator.
#
# Also, because we have this weird thing with new users,
# they should also have the check_new_user decorator.
#
# Thus each view should be structured like this:
#
#    @check_new_user
#    @analyzer_required
#    def my_view(request):
#        ...

from collections import defaultdict
from datetime import datetime, timedelta

from elasticutils.contrib.django import es_required_or_50x

from django.shortcuts import render

from fjord.analytics.forms import OccurrencesComparisonForm
from fjord.base.util import analyzer_required, check_new_user
from fjord.feedback.models import Product, ResponseMappingType


@check_new_user
@analyzer_required
def analytics_dashboard(request):
    """Main page for analytics related things"""
    template = 'analytics/analyzer/dashboard.html'
    return render(request, template)


@check_new_user
@analyzer_required
def analytics_products(request):
    """Products list view"""
    template = 'analytics/analyzer/products.html'
    products = Product.objects.all()
    return render(request, template, {
        'products': products
    })


@check_new_user
@analyzer_required
@es_required_or_50x(error_template='analytics/es_down.html')
def analytics_occurrences(request):
    template = 'analytics/analyzer/occurrences.html'

    first_facet_bi = None
    first_params = {}
    first_facet_total = 0

    second_facet_bi = None
    second_params = {}
    second_facet_total = 0

    if 'product' in request.GET:
        form = OccurrencesComparisonForm(request.GET)
        if form.is_valid():
            cleaned = form.cleaned_data

            # First item
            first_resp_s = (ResponseMappingType.search()
                            .filter(product=cleaned['product'])
                            .filter(locale__startswith='en'))

            first_params['product'] = cleaned['product']

            if cleaned['first_version']:
                first_resp_s = first_resp_s.filter(
                    version=cleaned['first_version'])
                first_params['version'] = cleaned['first_version']
            if cleaned['first_start_date']:
                first_resp_s = first_resp_s.filter(
                    created__gte=cleaned['first_start_date'])
                first_params['date_start'] = cleaned['first_start_date']
            if cleaned['first_end_date']:
                first_resp_s = first_resp_s.filter(
                    created__lte=cleaned['first_end_date'])
                first_params['date_end'] = cleaned['first_end_date']
            if cleaned['first_search_term']:
                first_resp_s = first_resp_s.query(
                    description__text=cleaned['first_search_term'])
                first_params['q'] = cleaned['first_search_term']

            if ('date_start' not in first_params
                and 'date_end' not in first_params):

                # FIXME - If there's no start date, then we want
                # "everything" so we use a hard-coded 2013-01-01 date
                # here to hack that.
                #
                # Better way might be to change the dashboard to allow
                # for an "infinite" range, but there's no other use
                # case for that and the ranges are done in the ui--not
                # in the backend.
                first_params['date_start'] = '2013-01-01'

            # Have to do raw because we want a size > 10.
            first_resp_s = first_resp_s.facet_raw(
                description_bigrams={
                    'terms': {
                        'field': 'description_bigrams',
                        'size': '30',
                    },
                    'facet_filter': first_resp_s._build_query()['filter']
                }
            )
            first_resp_s = first_resp_s[0:0]

            first_facet_total = first_resp_s.count()
            first_facet = first_resp_s.facet_counts()

            first_facet_bi = first_facet['description_bigrams']
            first_facet_bi = sorted(
                first_facet_bi, key=lambda item: -item['count'])

            if (cleaned['second_version']
                or cleaned['second_search_term']
                or cleaned['second_start_date']):

                second_resp_s = (ResponseMappingType.search()
                                .filter(product=cleaned['product'])
                                .filter(locale__startswith='en'))

                second_params['product'] = cleaned['product']

                if cleaned['second_version']:
                    second_resp_s = second_resp_s.filter(
                        version=cleaned['second_version'])
                    second_params['version'] = cleaned['second_version']
                if cleaned['second_start_date']:
                    second_resp_s = second_resp_s.filter(
                        created__gte=cleaned['second_start_date'])
                    second_params['date_start'] = cleaned['second_start_date']
                if cleaned['second_end_date']:
                    second_resp_s = second_resp_s.filter(
                        created__lte=cleaned['second_end_date'])
                    second_params['date_end'] = cleaned['second_end_date']
                if form.cleaned_data['second_search_term']:
                    second_resp_s = second_resp_s.query(
                        description__text=cleaned['second_search_term'])
                    second_params['q'] = cleaned['second_search_term']

                if ('date_start' not in second_params
                    and 'date_end' not in second_params):

                    # FIXME - If there's no start date, then we want
                    # "everything" so we use a hard-coded 2013-01-01 date
                    # here to hack that.
                    #
                    # Better way might be to change the dashboard to allow
                    # for an "infinite" range, but there's no other use
                    # case for that and the ranges are done in the ui--not
                    # in the backend.
                    second_params['date_start'] = '2013-01-01'

                # Have to do raw because we want a size > 10.
                second_resp_s = second_resp_s.facet_raw(
                    description_bigrams={
                        'terms': {
                            'field': 'description_bigrams',
                            'size': '30',
                        },
                        'facet_filter': second_resp_s._build_query()['filter']
                    }
                )
                second_resp_s = second_resp_s[0:0]

                second_facet_total = second_resp_s.count()
                second_facet = second_resp_s.facet_counts()

                second_facet_bi = second_facet['description_bigrams']
                second_facet_bi = sorted(
                    second_facet_bi, key=lambda item: -item['count'])

        permalink = request.build_absolute_uri()

    else:
        permalink = ''
        form = OccurrencesComparisonForm()

    # FIXME - We have responses that have no product set. This ignores
    # those. That's probably the right thing to do for the Occurrences Report
    # but maybe not.
    products = [prod for prod in ResponseMappingType.get_products() if prod]

    return render(request, template, {
        'permalink': permalink,
        'form': form,
        'products': products,
        'first_facet_bi': first_facet_bi,
        'first_params': first_params,
        'first_facet_total': first_facet_total,
        'first_normalization': round(first_facet_total * 1.0 / 1000, 3),
        'second_facet_bi': second_facet_bi,
        'second_params': second_params,
        'second_facet_total': second_facet_total,
        'second_normalization': round(second_facet_total * 1.0 / 1000, 3),
        'render_time': datetime.now(),
    })


@check_new_user
@analyzer_required
@es_required_or_50x(error_template='analytics/es_down.html')
def analytics_duplicates(request):
    """Shows all duplicate descriptions over the last n days"""
    template = 'analytics/analyzer/duplicates.html'

    n = 14

    responses = (ResponseMappingType.search()
                 .filter(created__gte=datetime.now() - timedelta(days=n))
                 .values_dict('description', 'happy', 'created', 'locale',
                              'user_agent', 'id')
                 .order_by('created').all())

    total_count = len(responses)

    response_dupes = {}
    for resp in responses:
        response_dupes.setdefault(resp['description'], []).append(resp)

    response_dupes = [
        (key, val) for key, val in response_dupes.items()
        if len(val) > 1
    ]

    # convert the dict into a list of tuples sorted by the number of
    # responses per tuple largest number first
    response_dupes = sorted(response_dupes, key=lambda item: len(item[1]) * -1)

    # duplicate_count -> count
    # i.e. "how many responses had 2 duplicates?"
    summary_counts = defaultdict(int)
    for desc, responses in response_dupes:
        summary_counts[len(responses)] = summary_counts[len(responses)] + 1
    summary_counts = sorted(summary_counts.items(), key=lambda item: item[0])

    return render(request, template, {
        'n': 14,
        'response_dupes': response_dupes,
        'render_time': datetime.now(),
        'summary_counts': summary_counts,
        'total_count': total_count,
    })
