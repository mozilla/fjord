from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from funfactory.urlresolvers import reverse
from mobility.decorators import mobile_template

from fjord.base.util import smart_bool
from fjord.feedback.forms import ResponseForm
from fjord.feedback import models


@mobile_template('feedback/{mobile/}thanks.html')
def thanks(request, template):
    return render(request, template)


def _handle_feedback_post(request):
    form = ResponseForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        # Most platforms aren't different enough between versions to care.
        # Windows is.
        platform = request.BROWSER.platform
        if platform == 'Windows':
            platform += ' ' + request.BROWSER.platform_version

        opinion = models.Response(
            # Data coming from the user
            happy=data['happy'],
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
            e = models.ResponseEmail(email=data['email'], opinion=opinion)
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


@csrf_protect
def desktop_stable_feedback(request):
    # Use two instances of the same form because the template changes the text
    # based on the value of ``happy``.
    forms = {
        'happy': ResponseForm(initial={'happy': 1}),
        'sad': ResponseForm(initial={'happy': 0}),
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


@csrf_protect
def mobile_stable_feedback(request):
    form = ResponseForm()
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


@csrf_exempt
@require_POST
def android_about_feedback(request):
    """A view specifically for Firefox for Android.

    Firefox for Android has a feedback form built in that generates
    POSTS directly to Input, and is always sad or ideas. Since Input no
    longer supports idea feedbacks, everything is Sad.
    """

    # Firefox for Android only sends up sad and idea responses, but it
    # uses the old `_type` variable from old Input. Tweak the data to do
    # what FfA means, not what it says.

    # Make `request.GET` mutable.
    request.GET = request.GET.copy()
    request.GET['happy'] = 0

    response, form = _handle_feedback_post(request)

    if response:
        return response

    # This means there was an error. Since FfA doesn't care about the
    # contents anyways, return an error code.
    return HttpResponse('', status=400)


# Mapping of prodchan values to views. If the parameter `formname` is passed to
# `feedback_router`, it will key into this dict.
feedback_routes = {
    'firefox.desktop.stable': desktop_stable_feedback,
    'firefox.android.stable': mobile_stable_feedback,
    'firefox.fxos.stable': mobile_stable_feedback,
}


@csrf_exempt
def feedback_router(request, formname=None, *args, **kwargs):
    """Determine a view to use, and call it.

    If formname is given, reference `feedback_routes` to look up a view.
    If `formname` is not passed, or isn't found in `feedback_routes`,
    asssume the user is either a stable desktop Firefox or a stable
    mobile Firefox based on the parsed UA, and serve them the appropriate
    page.
    """
    view = feedback_routes.get(formname)

    # Checks to see if `_type` is in the POST data and if so this is
    # coming from Firefox for Android which doesn't know anything
    # about csrf tokens. If that's the case, we send it to a view
    # specifically for FfA Otherwise we pass it to one of the normal
    # views, which enforces CSRF.
    #
    # FIXME: Remove this hairbrained monstrosity when we don't need to
    # support the method that Firefox for Android currently uses to
    # post feedback which worked with the old input.mozilla.org.
    if '_type' in request.POST:
        view = android_about_feedback

    if view is None:
        if request.BROWSER.mobile:
            view = mobile_stable_feedback
        else:
            view = desktop_stable_feedback

    return view(request, *args, **kwargs)
