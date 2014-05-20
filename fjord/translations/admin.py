from django.conf import settings
from django.contrib import admin
from django.shortcuts import render

from gengo import Gengo


def gengo_translator_view(request):
    if not settings.GENGO_PUBLIC_KEY or not settings.GENGO_PRIVATE_KEY:
        return render(request, 'admin/gengo_translator_view.html', {
            'settings': settings,
            'configured': False
        })

    gengo = Gengo(
        public_key=settings.GENGO_PUBLIC_KEY,
        private_key=settings.GENGO_PRIVATE_KEY,
        # FIXME - sandbox?
    )

    balance = gengo.getAccountBalance()

    balance = ' '.join([
        balance['response']['credits'],
        balance['response']['currency']]
    )

    return render(request, 'admin/gengo_translator_view.html', {
        'configured': True,
        'settings': settings,
        'balance': balance
    })


admin.site.register_view('gengo-translator-view', gengo_translator_view,
                         'Gengo - Maintenance')
