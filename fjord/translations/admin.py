from django.conf import settings
from django.contrib import admin
from django.shortcuts import render

from fjord.translations.gengo_utils import FjordGengo

from gengo import Gengo


def gengo_translator_view(request):
    if not settings.GENGO_PUBLIC_KEY or not settings.GENGO_PRIVATE_KEY:
        return render(request, 'admin/gengo_translator_view.html', {
            'settings': settings,
            'configured': False
        })

    gengo_api = FjordGengo()

    balance = gengo_api.get_balance()

    return render(request, 'admin/gengo_translator_view.html', {
        'configured': True,
        'settings': settings,
        'balance': balance
    })


admin.site.register_view('gengo-translator-view', gengo_translator_view,
                         'Gengo - Maintenance')
