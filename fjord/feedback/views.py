from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from funfactory.urlresolvers import reverse
from mobility.decorators import mobile_template

from fjord.base.util import smart_bool
from fjord.feedback.forms import SimpleForm
from fjord.feedback import models


@mobile_template('feedback/{mobile/}thanks.html')
def thanks(request, template):
    return render(request, template)


def _handle_feedback_post(request):
    form = SimpleForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        # Most platforms aren't different enough between versions to care.
        # Windows is.
        platform = request.BROWSER.platform
        if platform == 'Windows':
            platform += ' ' + request.BROWSER.platform_version

        if '_type' in request.POST:
            # If _type is in the POST data then, this is coming from
            # Firefox for Android which posted directly to the old
            # site which used _type. Feedback from Firefox for Android
            # is always sad. I kid you not.
            happy = False
        else:
            happy = data['happy']

        opinion = models.Simple(
            # Data coming from the user
            happy=happy,
            url=data['url'],
            description=data['description'],
            # Inferred data
            prodchan=_get_prodchan(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            browser=request.BROWSER.browser,
            browser_version=request.BROWSER.browser_version,
            platform=platform,
            locale=request.locale,
            # Data from mobile devices
            manufacturer=data.get('manufacturer', ''),
            device=data.get('device', ''),
        )
        opinion.save()

        if data['email_ok'] and data['email']:
            e = models.SimpleEmail(email=data['email'], opinion=opinion)
            e.save()

        return HttpResponseRedirect(reverse('thanks')), form

    # The user did something wrong.
    return None, form


def _get_prodchan(request):
    meta = request.BROWSER

    product = ''
    platform = ''
    channel = 'stable'

    if meta.browser == 'Firefox':
        product = 'firefox'
    else:
        product = 'unknown'

    if meta.platform == 'Android':
        platform = 'android'
    elif meta.platform == 'FirefoxOS':
        platform = 'fxos'
    elif product == 'firefox':
        platform = 'desktop'
    else:
        platform = 'unknown'

    return '{0}.{1}.{2}'.format(product, platform, channel)


def desktop_stable_feedback(request):
    # Use two instances of the same form because the template changes the text
    # based on the value of ``happy``.
    forms = {
        'happy': SimpleForm(initial={'happy': 1}),
        'sad': SimpleForm(initial={'happy': 0}),
    }

    if request.method == 'POST':
        response, form = _handle_feedback_post(request)
        if response:
            return response

        happy = smart_bool(request.POST.get('happy', None))
        if happy:
            forms['happy'] = form
        else:
            forms['sad'] = form

    return render(request, 'feedback/feedback.html', {'forms': forms})


def mobile_stable_feedback(request):
    form = SimpleForm()
    happy = None

    if request.method == 'POST':
        response, form = _handle_feedback_post(request)
        if response:
            return response
        happy = smart_bool(request.POST.get('happy', None), None)

    return render(request, 'feedback/mobile/feedback.html', {
        'form': form,
        'happy': happy,
    })


# Mapping of prodchan values to views. If the parameter `formname` is passed to
# `feedback_router`, it will key into this dict.
feedback_routes = {
    'firefox.desktop.stable': desktop_stable_feedback,
    'firefox.android.stable': mobile_stable_feedback,
    'firefox.fxos.stable': mobile_stable_feedback,
}


@csrf_protect
def csrf_checked_feedback_router(request, *args, **kwargs):
    return feedback_router_actual(request, *args, **kwargs)


def feedback_router_actual(request, formname=None, *args, **kwargs):
    """Determine a view to use, and call it.

    If formname is given, reference `feedback_routes` to look up a view.
    If `formname` is not passed, or isn't found in `feedback_routes`,
    asssume the user is either a stable desktop Firefox or a stable
    mobile Firefox based on the parsed UA, and serve them the appropriate
    page.
    """
    view = feedback_routes.get(formname)

    if view is None:
        if request.BROWSER.mobile:
            view = mobile_stable_feedback
        else:
            view = desktop_stable_feedback
    return view(request, *args, **kwargs)


@csrf_exempt
def feedback_router(request, *args, **kwargs):
    """Handles the feedback view"""
    # Checks to see if `_type` is in the POST data and if so this is
    # coming from Firefox for Android which doesn't know anything
    # about csrf tokens. If that's the case, we just let it through.
    # Otherwise we pass it to csrf_checked_feedback_router to check
    # for csrf and deny if appropriate.
    #
    # FIXME: Remove this hairbrained monstrosity when we don't need to
    # support the method that Firefox for Android currently uses to
    # post feedback which worked with the old input.mozilla.org.
    if '_type' in request.POST:
        return feedback_router_actual(request, *args, **kwargs)

    return csrf_checked_feedback_router(request, *args, **kwargs)
