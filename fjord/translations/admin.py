from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.module_loading import import_by_path

from .gengo_utils import FjordGengo
from .models import GengoJob, GengoOrder
from .tasks import create_translation_tasks
from .utils import locale_equals_language
from fjord.base.util import smart_date, smart_str
from fjord.feedback.models import Product
from fjord.journal.models import Record


class GengoJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'content_type',
        'object_id',
        'content_object',
        'src_lang',
        'src_field',
        'dst_lang',
        'dst_field',
        'status',
        'order',
        'created',
        'completed'
    )
    list_filter = ('status', 'content_type')

admin.site.register(GengoJob, GengoJobAdmin)


class GengoOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_id',
        'status',
        'created',
        'completed'
    )
    list_filter = ('status',)

admin.site.register(GengoOrder, GengoOrderAdmin)


def gengo_translator_view(request):
    """Covers Gengo-specific translation system status"""
    products = Product.objects.all()
    balance = None
    configured = False
    gengo_languages = None
    missing_prod_locales = None

    if settings.GENGO_PUBLIC_KEY and settings.GENGO_PRIVATE_KEY:
        gengo_api = FjordGengo()
        balance = gengo_api.get_balance()
        configured = True

        # Figure out the list of languages Gengo supports and relate them
        # to PROD locales.
        languages = sorted(gengo_api.get_languages(raw=True)['response'],
                           key=lambda item: item['lc'])
        gengo_languages = []
        PROD_LANG = settings.PROD_LANGUAGES
        for lang in languages:
            lang_lc = lang['lc']
            prod_langs = [item for item in PROD_LANG
                          if locale_equals_language(item, lang_lc)]
            prod_langs = ' '.join(prod_langs)

            gengo_languages.append(
                (lang_lc, lang['language'], prod_langs)
            )

        # Figure out the list of PROD locales that don't have a Gengo
        # supported language. (Yes, this conflates locale with
        # language which isn't great, but is good enough for now.)
        languages = gengo_api.get_languages()
        missing_prod_locales = []
        for prod_lang in PROD_LANG:
            langs = [item for item in languages
                     if locale_equals_language(prod_lang, item)]
            if langs:
                continue
            missing_prod_locales.append(prod_lang)

        # How many orders have we created/completed in the last week
        # day-by-day?
        seven_days = datetime.now() - timedelta(days=7)

        orders = GengoOrder.objects.filter(created__gte=seven_days)
        created_by_day = {}
        for order in orders:
            dt = order.created.strftime('%Y-%m-%d')
            created_by_day.setdefault(dt, []).append(order)

        orders = GengoOrder.objects.filter(completed__gte=seven_days)
        completed_by_day = {}
        for order in orders:
            dt = order.completed.strftime('%Y-%m-%d')
            completed_by_day.setdefault(dt, []).append(order)

        # Get date labels in YYYY-mm-dd form for the last 7 days
        days = [
            (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(7)
        ]

        seven_days_of_orders = []
        for day in sorted(days):
            seven_days_of_orders.append(
                (day,
                 len(created_by_day.get(day, [])),
                 len(completed_by_day.get(day, [])))
            )

        outstanding = [
            {
                'id': order.id,
                'order_id': order.order_id,
                'created': order.created,
                'total_jobs': order.gengojob_set.all().count(),
                'completed_jobs': order.completed_jobs().count(),
                'outstanding_jobs': order.outstanding_jobs().count(),
            }
            for order in GengoOrder.objects.filter(completed__isnull=True)]

    return render(request, 'admin/gengo_translator_view.html', {
        'title': 'Translations - Gengo Maintenance',
        'configured': configured,
        'settings': settings,
        'products': products,
        'outstanding': outstanding,
        'seven_days_of_orders': seven_days_of_orders,
        'balance': balance,
        'gengo_languages': gengo_languages,
        'missing_prod_locales': missing_prod_locales,
    })


admin.site.register_view('gengo-translator-view', gengo_translator_view,
                         'Translations - Gengo Maintenance')


def translations_management_backfill_view(request):
    """Takes start and end dates and a model and backfills translations"""
    date_start = smart_date(request.POST.get('date_start'))
    date_end = smart_date(request.POST.get('date_end'))
    model = smart_str(request.POST.get('model'))

    if request.method == 'POST' and date_start and date_end and model:
        # NB: We just let the errors propagate because this is an
        # admin page. That way we get a traceback and all that detail.

        # We add one day to date_end so that it picks up the entire day of
        # date_end.
        #
        # FIXME: We should do this in a less goofy way.
        date_end = date_end + timedelta(days=1)

        model_cls = import_by_path(model)

        # FIXME: This assumes the model has a "created" field. If it
        # doesn't, then this breaks. When we have another model that we
        # want to translate, we can figure out how to generalize this
        # then.
        objects = model_cls.objects.filter(
            created__gte=date_start,
            created__lte=date_end
        )

        total_jobs = 0

        for instance in objects:
            total_jobs += len(create_translation_tasks(instance))

        messages.success(request, '%s jobs added' % total_jobs)
        return HttpResponseRedirect(request.path)

    from fjord.translations.tasks import REGISTERED_MODELS
    model_classes = [
        cls.__module__ + '.' + cls.__name__
        for cls in REGISTERED_MODELS
    ]

    return render(request, 'admin/translations_backfill.html', {
        'title': 'Translations - General Maintenance - Backfill',
        'settings': settings,
        'model_classes': model_classes,
        'date_start': request.POST.get('date_start', ''),
        'date_end': request.POST.get('date_end', ''),
        'model': request.POST.get('model', '')
    })


admin.site.register_view(
    'translations-management-backfill-view',
    translations_management_backfill_view,
    'Translations - General - Backfill')


def translations_management_view(request):
    """Covers general translation system status"""
    # We want to order the record objects by whichever column was
    # picked. We have some handling for reverse sort, but not in the
    # form.
    columns = ('src', 'type', 'action', 'msg', 'created', 'metadata')

    order = request.GET.get('order', '-created')
    if order.replace('-', '') not in columns:
        order = '-created'

    return render(request, 'admin/translations.html', {
        'title': 'Translations - General Maintenance',
        'settings': settings,
        'products': Product.objects.all(),
        'records': Record.objects.recent('translations').order_by(order),
    })


admin.site.register_view(
    'translations-management-view', translations_management_view,
    'Translations - General')
