from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from funfactory.urlresolvers import reverse
from session_csrf import anonymous_csrf_exempt

from fjord.base.util import smart_bool
from fjord.feedback.forms import SimpleForm
from fjord.feedback import models


def thanks(request):
    return render(request, 'feedback/thanks.html')


def desktop_stable_feedback(request, template=None):
    # Use two instances of the same form because the template changes the text
    # based on the value of ``happy``.
    forms = {
        'happy': SimpleForm(initial={'happy': 1}),
        'sad': SimpleForm(initial={'happy': 0}),
    }

    if request.method == 'POST':
        form = SimpleForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Most platforms aren't different enough between versions to care.
            # Windows is.
            platform = request.BROWSER.platform
            if platform == 'Windows':
                platform += ' ' + request.BROWSER.platform_version

            opinion = models.Simple(
                # Data coming from the user
                happy=data['happy'],
                url=data['url'],
                description=data['description'],
                # Inferred data
                prodchan='firefox.desktop.stable',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                browser=request.BROWSER.browser,
                browser_version=request.BROWSER.browser_version,
                platform=platform,
                locale=request.locale,
            )
            opinion.save()

            if data['email_ok'] and data['email']:
                e = models.SimpleEmail(email=data['email'], opinion=opinion)
                e.save()

            return HttpResponseRedirect(reverse('thanks'))
        else:
            # The user did something wrong. Update the appropriate form, so
            # the errors show correctly.
            happy = smart_bool(request.POST.get('happy', None))
            if happy:
                forms['happy'] = form
            else:
                forms['sad'] = form

    return render(request, 'feedback/feedback.html', {'forms': forms})


feedback_routes = {
    'firefox.desktop.stable': desktop_stable_feedback,
    None: desktop_stable_feedback,
}


@anonymous_csrf_exempt
def feedback_router(request, formname=None, *args, **kwargs):
    # TODO: Route based on user agent detection.
    view = feedback_routes[formname]
    return view(request, *args, **kwargs)
