from django.conf import settings
from django.contrib import admin
from django.shortcuts import render

from fjord.feedback.models import Product
from fjord.translations.gengo_utils import FjordGengo


def gengo_translator_view(request):
    gengo_machiners = Product.objects.filter(translation_system='gengo_machine')
    balance = None
    configured = False

    if settings.GENGO_PUBLIC_KEY and settings.GENGO_PRIVATE_KEY:
        gengo_api = FjordGengo()
        balance = gengo_api.get_balance()
        configured = True

    return render(request, 'admin/gengo_translator_view.html', {
        'configured': configured,
        'settings': settings,
        'gengo_machiners': gengo_machiners,
        'balance': balance
    })


admin.site.register_view('gengo-translator-view', gengo_translator_view,
                         'Gengo - Maintenance')
