from django.conf import settings
from django.contrib import admin
from django.shortcuts import render

from fjord.feedback.models import Product
from fjord.translations.gengo_utils import FjordGengo


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
            if lang_lc in PROD_LANG:
                prod_lang = lang_lc
            else:
                prod_lang = [item for item in PROD_LANG
                             if item.startswith(lang_lc) or lang_lc.startswith(item)]
                prod_lang = ' '.join(prod_lang)

            gengo_languages.append(
                (lang_lc, lang['language'], prod_lang)
            )

        # Figure out the list of PROD locales that don't have a Gengo
        # supported language. (Yes, this conflates locale with
        # language which isn't great, but is good enough for now.)
        languages = gengo_api.get_languages()
        missing_prod_locales = []
        for lang in PROD_LANG:
            if (lang in languages
                or ([item for item in languages
                     if item.startswith(lang) or lang.startswith(item)])):
                continue
            missing_prod_locales.append(lang)

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
