from mobility.decorators import mobile_template
from django.http import HttpResponse
from django.shortcuts import render

from fjord.feedback.forms import SimpleForm
from fjord.feedback import models



def feedback_router(request, *args, **kwargs):
    # Eventually route based on user agent. For now just go ahead.
    return desktop_stable_feedback(request, *args, **kwargs)


@mobile_template('{mobile/}feedback.html')
def desktop_stable_feedback(request, template=None):
    forms = {
        'happy': SimpleForm(initial={'happy': True}),
        'sad': SimpleForm(initial={'happy': False}),
    }

    if request.method == 'POST':
        form = SimpleForm(request.POST)
        if form.is_valid():
            # Most platforms aren't different enough between versions to care.
            # Windows is.
            platform = request.BROWSER.platform
            if platform == 'Windows':
                platform += ' ' + request.BROWSER.platform_version

            opinion = models.Simple(
                # Data coming from the user
                happy = form.cleaned_data['happy'],
                url = form.cleaned_data['url'],
                description = form.cleaned_data['description'],
                # Inferred data
                prodchan = 'firefox.desktop.stable',
                user_agent = request.META.get('HTTP_USER_AGENT', ''),
                browser = request.BROWSER.browser,
                browser_version = request.BROWSER.browser_version,
                platform = platform,
                locale = request.locale,
            )
            opinion.save()
            return HttpResponse(str(opinion))
        else:
            if request.POST.get('happy'):
                forms['happy'] = form
            else:
                forms['sad'] = form

    return render(request, template, {'forms': forms})
