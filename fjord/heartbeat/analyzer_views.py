from datetime import datetime
from pprint import pformat

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView
from django.utils.decorators import method_decorator

from fjord.base.utils import analyzer_required, check_new_user
from fjord.heartbeat.forms import SurveyCreateForm
from fjord.heartbeat.models import Answer, Survey
from fjord.journal.models import Record


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
