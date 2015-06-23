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
#
# Also, since it's just analyzers, everyone is expected to speak
# English. Ergo, there's no localization here.

from datetime import date, datetime, timedelta
from pprint import pformat
import csv

from elasticsearch_dsl import F

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_bytes
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.utils.decorators import method_decorator

from fjord.analytics.forms import (
    ProductsUpdateForm,
    SurveyCreateForm
)
from fjord.analytics.utils import counts_to_options, zero_fill
from fjord.base.helpers import locale_name
from fjord.base.utils import (
    analyzer_required,
    check_new_user,
    smart_int,
    smart_date
)
from fjord.feedback.helpers import country_name
from fjord.feedback.models import Product, Response, ResponseDocType
from fjord.heartbeat.models import Answer, Survey
from fjord.journal.models import Record
from fjord.search.index import es_required_or_50x
from fjord.search.utils import es_error_statsd


@check_new_user
@analyzer_required
def hb_data(request, answerid=None):
    """View for hb data that shows one or all of the answers"""
    VALID_SORTBY_FIELDS = ('id', 'received_ts', 'updated_ts')

    sortby = 'id'
    answer = None
    answers = []
    survey = None
    showdata = None

    if answerid is not None:
        answer = Answer.objects.get(id=answerid)

    else:
        sortby = request.GET.get('sortby', sortby)
        if sortby not in VALID_SORTBY_FIELDS:
            sortby = 'id'

        page = request.GET.get('page')
        answers = Answer.objects.order_by('-' + sortby)
        survey = request.GET.get('survey', survey)
        showdata = request.GET.get('showdata', None)

        if showdata:
            if showdata == 'test':
                answers = answers.filter(is_test=True)
            elif showdata == 'notest':
                answers = answers.exclude(is_test=True)
            else:
                showdata = 'all'
        else:
            showdata = 'all'

        if survey:
            try:
                survey = Survey.objects.get(id=survey)
                answers = answers.filter(survey_id=survey)
            except Survey.DoesNotExist:
                survey = None

        paginator = Paginator(answers, 100)
        try:
            answers = paginator.page(page)
        except PageNotAnInteger:
            answers = paginator.page(1)
        except EmptyPage:
            answers = paginator.page(paginator.num_pages)

    def fix_ts(ts):
        ts = float(ts / 1000)
        return datetime.fromtimestamp(ts)

    return render(request, 'analytics/analyzer/hb_data.html', {
        'sortby': sortby,
        'answer': answer,
        'answers': answers,
        'fix_ts': fix_ts,
        'pformat': pformat,
        'survey': survey,
        'surveys': Survey.objects.all(),
        'showdata': showdata,
    })


@check_new_user
@analyzer_required
def hb_errorlog(request, errorid=None):
    """View for hb errorlog that shows one or all of the errors"""
    error = None
    errors = []

    if errorid is not None:
        error = Record.objects.get(id=errorid)

    else:
        page = request.GET.get('page')
        paginator = Paginator(
            Record.objects.filter(app='heartbeat').order_by('-id'), 100)
        try:
            errors = paginator.page(page)
        except PageNotAnInteger:
            errors = paginator.page(1)
        except EmptyPage:
            errors = paginator.page(paginator.num_pages)

    return render(request, 'analytics/analyzer/hb_errorlog.html', {
        'error': error,
        'errors': errors,
        'pformat': pformat
    })


@check_new_user
@analyzer_required
def analytics_dashboard(request):
    """Main page for analytics related things"""
    template = 'analytics/analyzer/dashboard.html'
    return render(request, template)


def _analytics_search_export(request, opinions_s):
    """Handles CSV export for analytics search

    This only exports MAX_OPINIONS amount. It adds a note to the top
    about that if the results are truncated.

    """
    MAX_OPINIONS = 1000

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(
        datetime.now().strftime('%Y%m%d_%H%M_search_export.csv'))

    keys = Response.get_export_keys(confidential=True)
    total_opinions = opinions_s.count()

    opinions_s = opinions_s.fields('id')[:MAX_OPINIONS].execute()

    # We convert what we get back from ES to what's in the db so we
    # can get all the information.
    opinions = Response.objects.filter(
        id__in=[mem['id'][0] for mem in opinions_s])

    writer = csv.writer(response)

    # Specify what this search is
    writer.writerow(['URL: {0}'.format(request.get_full_path())])
    writer.writerow(['Params: ' +
                     ' '.join(['{0}: {1}'.format(key, val)
                               for key, val in request.GET.items()])])

    # Add note if we truncated.
    if total_opinions > MAX_OPINIONS:
        writer.writerow(['Truncated {0} rows.'.format(
            total_opinions - MAX_OPINIONS)])

    # Write headers row.
    writer.writerow(keys)

    # Write opinion rows.
    for op in opinions:
        writer.writerow([force_bytes(getattr(op, key)) for key in keys])

    return response


@check_new_user
@analyzer_required
@es_required_or_50x(error_template='analytics/es_down.html')
@es_error_statsd
def analytics_search(request):
    template = 'analytics/analyzer/search.html'

    output_format = request.GET.get('format', None)
    page = smart_int(request.GET.get('page', 1), 1)

    # Note: If we add additional querystring fields, we need to add
    # them to generate_dashboard_url.
    search_happy = request.GET.get('happy', None)
    search_platform = request.GET.get('platform', None)
    search_locale = request.GET.get('locale', None)
    search_product = request.GET.get('product', None)
    search_version = request.GET.get('version', None)
    search_query = request.GET.get('q', None)
    search_date_start = smart_date(
        request.GET.get('date_start', None), fallback=None)
    search_date_end = smart_date(
        request.GET.get('date_end', None), fallback=None)
    search_bigram = request.GET.get('bigram', None)
    selected = request.GET.get('selected', None)

    search_has_email = request.GET.get('has_email', None)
    search_country = request.GET.get('country', None)
    search_domain = request.GET.get('domain', None)
    search_api = smart_int(request.GET.get('api', None), fallback=None)
    search_source = request.GET.get('source', None)
    search_campaign = request.GET.get('campaign', None)
    search_organic = request.GET.get('organic', None)

    filter_data = []
    current_search = {'page': page}

    search = ResponseDocType.docs.search()
    f = F()
    # If search happy is '0' or '1', set it to False or True, respectively.
    search_happy = {'0': False, '1': True}.get(search_happy, None)
    if search_happy in [False, True]:
        f &= F('term', happy=search_happy)
        current_search['happy'] = int(search_happy)

    # If search has_email is '0' or '1', set it to False or True,
    # respectively.
    search_has_email = {'0': False, '1': True}.get(search_has_email, None)
    if search_has_email in [False, True]:
        f &= F('term', has_email=search_has_email)
        current_search['has_email'] = int(search_has_email)

    def unknown_to_empty(text):
        """Convert "Unknown" to "" to support old links"""
        return u'' if text.lower() == u'unknown' else text

    if search_platform is not None:
        f &= F('term', platform=unknown_to_empty(search_platform))
        current_search['platform'] = search_platform
    if search_locale is not None:
        f &= F('term', locale=unknown_to_empty(search_locale))
        current_search['locale'] = search_locale
    if search_product is not None:
        f &= F('term', product=unknown_to_empty(search_product))
        current_search['product'] = search_product

        # Only show the version if there's a product.
        if search_version is not None:
            # Note: We only filter on version if we're filtering on
            # product.
            f &= F('term', version=unknown_to_empty(search_version))
            current_search['version'] = search_version

        # Only show the country if the product is Firefox OS.
        if search_country is not None and search_product == 'Firefox OS':
            f &= F('term', country=unknown_to_empty(search_country))
            current_search['country'] = search_country
    if search_domain is not None:
        f &= F('term', url_domain=unknown_to_empty(search_domain))
        current_search['domain'] = search_domain
    if search_api is not None:
        f &= F('term', api=search_api)
        current_search['api'] = search_api

    if search_date_start is None and search_date_end is None:
        selected = '7d'

    if search_date_end is None:
        search_date_end = date.today()
    if search_date_start is None:
        search_date_start = search_date_end - timedelta(days=7)

    # If the start and end dates are inverted, switch them into proper
    # chronological order
    search_date_start, search_date_end = sorted(
        [search_date_start, search_date_end])

    current_search['date_end'] = search_date_end.strftime('%Y-%m-%d')
    f &= F('range', created={'lte': search_date_end})

    current_search['date_start'] = search_date_start.strftime('%Y-%m-%d')
    f &= F('range', created={'gte': search_date_start})

    if search_query:
        current_search['q'] = search_query
        search = search.query('simple_query_string', query=search_query,
                              fields=['description'])

    if search_bigram is not None:
        f &= F('terms', description_bigrams=search_bigram)
        filter_data.append({
            'display': 'Bigram',
            'name': 'bigram',
            'options': [{
                'count': 'all',
                'name': search_bigram,
                'display': search_bigram,
                'value': search_bigram,
                'checked': True
            }]
        })

    if search_source is not None:
        f &= F('term', source=search_source)
        current_search['source'] = search_source
    if search_campaign is not None:
        f &= F('term', campaign=search_campaign)
        current_search['campaign'] = search_campaign
    search_organic = {'0': False, '1': True}.get(search_organic, None)
    if search_organic in [False, True]:
        f &= F('term', organic=search_organic)
        current_search['organic'] = int(search_organic)

    search = search.filter(f).sort('-created')

    # If they're asking for a CSV export, then send them to the export
    # screen.
    if output_format == 'csv':
        return _analytics_search_export(request, search)

    original_search = search._clone()

    # Search results and pagination
    if page < 1:
        page = 1
    page_count = 50
    start = page_count * (page - 1)
    end = start + page_count

    search_count = search.count()
    search_results = search.fields('id')[start:end].execute()
    opinion_page_ids = [mem['id'][0] for mem in search_results]

    # We convert what we get back from ES to what's in the db so we
    # can get all the information.
    opinion_page = Response.objects.filter(id__in=opinion_page_ids)

    # Add navigation aggregations
    counts = {
        'happy': {},
        'has_email': {},
        'platform': {},
        'locale': {},
        'country': {},
        'product': {},
        'version': {},
        'url_domain': {},
        'api': {},
        'source': {},
        'campaign': {},
        'organic': {},
    }

    for name in counts.keys():
        search.aggs.bucket(name, 'terms', field=name, size=1000)

    results = search.execute()

    # Extract the value and doc_count for the various facets we do
    # faceted navigation on.
    for name in counts.keys():
        buckets = getattr(results.aggregations, name)['buckets']
        for bucket in buckets:
            key = bucket['key']
            # Convert from 'T'/'F' to True/False
            if key in ['T', 'F']:
                key = (key == 'T')
            counts[name][key] = bucket['doc_count']

    def empty_to_unknown(text):
        return 'Unknown' if text == u'' else text

    filter_data.extend([
        counts_to_options(
            counts['happy'].items(),
            name='happy',
            display='Sentiment',
            display_map={True: 'Happy', False: 'Sad'},
            value_map={True: 1, False: 0},
            checked=search_happy),
        counts_to_options(
            counts['has_email'].items(),
            name='has_email',
            display='Has email',
            display_map={True: 'Yes', False: 'No'},
            value_map={True: 1, False: 0},
            checked=search_has_email),
        counts_to_options(
            counts['product'].items(),
            name='product',
            display='Product',
            display_map=empty_to_unknown,
            checked=search_product)
    ])
    # Only show the version if we're showing a specific
    # product.
    if search_product:
        filter_data.append(
            counts_to_options(
                counts['version'].items(),
                name='version',
                display='Version',
                display_map=empty_to_unknown,
                checked=search_version)
        )
        # Only show the country if the product is Firefox OS.
        if search_product == 'Firefox OS':
            filter_data.append(
                counts_to_options(
                    counts['country'].items(),
                    name='country',
                    display='Country',
                    checked=search_country,
                    display_map=country_name),
            )

    filter_data.extend(
        [
            counts_to_options(
                counts['platform'].items(),
                name='platform',
                display='Platform',
                display_map=empty_to_unknown,
                checked=search_platform),
            counts_to_options(
                counts['locale'].items(),
                name='locale',
                display='Locale',
                checked=search_locale,
                display_map=locale_name),
            counts_to_options(
                counts['url_domain'].items(),
                name='domain',
                display='Domain',
                checked=search_domain,
                display_map=empty_to_unknown),
            counts_to_options(
                counts['api'].items(),
                name='api',
                display='API version',
                checked=search_api,
                display_map=empty_to_unknown),
            counts_to_options(
                counts['organic'].items(),
                name='organic',
                display='Organic',
                display_map={True: 'Yes', False: 'No'},
                value_map={True: 1, False: 0},
                checked=search_organic),
            counts_to_options(
                counts['source'].items(),
                name='source',
                display='Source',
                checked=search_source,
                display_map=empty_to_unknown),
            counts_to_options(
                counts['campaign'].items(),
                name='campaign',
                display='Campaign',
                checked=search_campaign,
                display_map=empty_to_unknown),
        ]
    )

    # Histogram data
    happy_data = []
    sad_data = []

    (original_search.aggs
     .bucket('histogram', 'date_histogram', field='created', interval='day')
     .bucket('per_sentiment', 'terms', field='happy')
    )

    results = original_search.execute()
    buckets = results.aggregations['histogram']['buckets']

    happy_data = {}
    sad_data = {}
    for bucket in buckets:
        # value -> count
        val_counts = dict(
            (item['key'], item['doc_count'])
            for item in bucket['per_sentiment']['buckets']
        )
        # key is ms since epoch here which is what the frontend wants, so
        # we can just leave it.
        happy_data[bucket['key']] = val_counts.get('T', 0)
        sad_data[bucket['key']] = val_counts.get('F', 0)

    zero_fill(search_date_start, search_date_end, [happy_data, sad_data])
    histogram = [
        {'label': 'Happy', 'name': 'happy',
         'data': sorted(happy_data.items())},
        {'label': 'Sad', 'name': 'sad',
         'data': sorted(sad_data.items())},
    ]

    return render(request, template, {
        'opinions': opinion_page,
        'opinion_count': search_count,
        'filter_data': filter_data,
        'histogram': histogram,
        'page': page,
        'prev_page': page - 1 if start > 0 else None,
        'next_page': page + 1 if end < search_count else None,
        'current_search': current_search,
        'selected': selected,
    })


class ProductsUpdateView(FormView):
    """An administrator view for showing, adding, and updating the products."""
    template_name = 'analytics/analyzer/addproducts.html'
    form_class = ProductsUpdateForm
    success_url = 'products'

    @method_decorator(check_new_user)
    @method_decorator(analyzer_required)
    def dispatch(self, *args, **kwargs):
        return super(ProductsUpdateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if 'pk' in request.GET:
            self.object = get_object_or_404(Product, pk=request.GET['pk'])
        return super(ProductsUpdateView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProductsUpdateView, self).get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        return context

    def get_form_kwargs(self):
        kwargs = super(ProductsUpdateView, self).get_form_kwargs()
        if hasattr(self, 'object'):
            kwargs['instance'] = self.object
        return kwargs

    def form_valid(self, form):
        try:
            instance = Product.objects.get(db_name=form.data.get('db_name'))
            instance.slug = form.data.get('slug') or instance.slug
            instance.display_name = (form.data.get('display_name') or
                                     instance.display_name)
            instance.notes = form.data.get('notes') or instance.notes
            instance.enabled = form.data.get('enabled') or False
            instance.on_dashboard = form.data.get('on_dashboard') or False
            instance.on_picker = form.data.get('on_picker') or False
            instance.browser = form.data.get('browser') or u''
            instance.browser_data_browser = (
                form.data.get('browser_data_browser') or u''
            )
            self.object = instance.save()
        except Product.DoesNotExist:
            self.object = form.save()
        return super(ProductsUpdateView, self).form_valid(form)


class SurveyCreateView(CreateView):
    model = Survey
    template_name = 'analytics/analyzer/hb_surveys.html'
    success_url = reverse_lazy('hb_surveys')
    form_class = SurveyCreateForm

    @method_decorator(check_new_user)
    @method_decorator(analyzer_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SurveyCreateView, self).get_context_data(**kwargs)
        page = self.request.GET.get('page')
        paginator = Paginator(Survey.objects.order_by('-created'), 25)
        try:
            surveys = paginator.page(page)
        except PageNotAnInteger:
            surveys = paginator.page(1)
        except EmptyPage:
            surveys = paginator.page(paginator.num_pages)

        context['surveys'] = surveys
        context['update'] = False
        return context


class SurveyUpdateView(UpdateView):
    model = Survey
    template_name = 'analytics/analyzer/hb_surveys.html'
    success_url = reverse_lazy('hb_surveys')
    form_class = SurveyCreateForm

    @method_decorator(check_new_user)
    @method_decorator(analyzer_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SurveyUpdateView, self).get_context_data(**kwargs)
        page = self.request.GET.get('page')
        paginator = Paginator(Survey.objects.order_by('-created'), 25)
        try:
            surveys = paginator.page(page)
        except PageNotAnInteger:
            surveys = paginator.page(1)
        except EmptyPage:
            surveys = paginator.page(paginator.num_pages)

        context['surveys'] = surveys
        context['update'] = True
        return context
