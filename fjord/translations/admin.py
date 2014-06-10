from django.conf import settings
from django.contrib import admin
from django.shortcuts import render

from .gengo_utils import FjordGengo
from .utils import locale_equals_language
from fjord.feedback.models import Product
from fjord.journal.models import Record


def gengo_translator_view(request):
    gengo_machiners = Product.objects.filter(translation_system='gengo_machine')
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

    return render(request, 'admin/gengo_translator_view.html', {
        'title': 'Gengo Maintenace Admin',
        'configured': configured,
        'settings': settings,
        'gengo_machiners': gengo_machiners,
        'balance': balance,
        'gengo_languages': gengo_languages,
        'missing_prod_locales': missing_prod_locales,
    })


admin.site.register_view('gengo-translator-view', gengo_translator_view,
                         'Gengo - Maintenance')


def translations_management_view(request):
    # We want to order the record objects by whichever column was
    # picked. We have some handling for reverse sort, but not in the
    # form.
    columns = ('src', 'type', 'action', 'msg', 'created', 'metadata')

    order = request.GET.get('order', '-created')
    if order.replace('-', '') not in columns:
        order = '-created'

    return render(request, 'admin/translations.html', {
        'title': 'Translations Maintenance',
        'settings': settings,
        'products': Product.objects.all(),
        'records': Record.objects.recent('translations').order_by(order),
    })


admin.site.register_view(
    'translations-management-view', translations_management_view,
    'Translations - Management')
