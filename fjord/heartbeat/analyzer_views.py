from datetime import datetime
from pprint import pformat

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView
from django.utils.decorators import method_decorator

from fjord.base.utils import analyzer_required, check_new_user
from fjord.heartbeat.forms import SurveyCreateForm
from fjord.heartbeat.healthcheck import (
    email_healthchecks,
    MAILINGLIST,
    run_healthchecks,
    SEVERITY
)
from fjord.heartbeat.models import Answer, Survey
from fjord.journal.models import Record
from fjord.mailinglist.utils import get_recipients


@check_new_user
@analyzer_required
def hb_healthcheck(request):
    """View for viewing healthchecks and kicking off a healthcheck email"""
    ml_recipients = get_recipients(MAILINGLIST)

    results = run_healthchecks()

    # If they did a POST, it means they want to email the results to the
    # mailing list.
    if request.method == 'POST':
        email_healthchecks(results)

    return render(request, 'analytics/analyzer/hb_healthcheck.html', {
        'results': results,
        'MAILINGLIST': MAILINGLIST,
        'ml_recipients': ml_recipients,
        'severity_name': SEVERITY
    })


@check_new_user
@analyzer_required
def hb_data(request, answerid=None):
    """View for hb data that shows one or all of the answers"""
    VALID_SORTBY_FIELDS = ('id', 'received_ts', 'updated_ts')

    ALL_FIELDS = [
        'id', 'received_ts', 'updated_ts', 'experiment_version',
        'response_version', 'person_id', 'survey_id',
        'flow_id', 'question_id', 'question_text', 'variation_id',
        'score', 'max_score', 'flow_began_ts', 'flow_offered_ts',
        'flow_voted_ts', 'flow_engaged_ts', 'platform', 'channel',
        'version', 'locale', 'country', 'build_id', 'partner_id',
        'profile_age', 'profile_usage', 'addons', 'extra'
    ]

    DEFAULT_FIELDS = [
        'id', 'received_ts', 'updated_ts', 'experiment_version',
        'response_version', 'person_id', 'survey_id', 'flow_id',
        'question_id', 'variation_id', 'score', 'max_score',
        'flow_began_ts', 'flow_voted_ts', 'platform', 'channel',
        'locale'
    ]

    sortby = 'id'
    answer = None
    answers = []
    fields = []
    survey = None
    showdata_filter = None

    if answerid is not None:
        answer = Answer.objects.get(id=answerid)

    else:
        # Get fields and split on comma, then get rid of empty fields.
        fields = request.GET.get('fields', '').split(',')

        # Nix any fields that don't exist
        fields = [field for field in fields if field in ALL_FIELDS]

        # If we have no fields, then use default_fields.
        fields = fields or DEFAULT_FIELDS

        sortby = request.GET.get('sortby', sortby)
        if sortby not in VALID_SORTBY_FIELDS:
            sortby = 'id'

        page = request.GET.get('page')
        answers = Answer.objects.order_by('-' + sortby)
        survey_filter = request.GET.get('survey', survey)
        showdata_filter = request.GET.get('showdata', None)

        if showdata_filter:
            if showdata_filter == 'test':
                answers = answers.filter(is_test=True)
            elif showdata_filter == 'notest':
                answers = answers.exclude(is_test=True)
            else:
                showdata_filter = 'all'
        else:
            showdata_filter = 'all'

        if survey_filter:
            try:
                survey = Survey.objects.get(id=survey_filter)
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
        'all_fields': ALL_FIELDS,
        'fields': fields,
        'sortby': sortby,
        'answer': answer,
        'answers': answers,
        'fix_ts': fix_ts,
        'getattr': getattr,
        'pformat': pformat,
        'survey': survey,
        'surveys': Survey.objects.all(),
        'showdata': showdata_filter,
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
