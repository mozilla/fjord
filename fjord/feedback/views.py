from functools import wraps

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from funfactory.urlresolvers import reverse
from mobility.decorators import mobile_template
from rest_framework import generics

from fjord.base.browsers import UNKNOWN
from fjord.base.util import smart_bool
from fjord.feedback.forms import ResponseForm
from fjord.feedback import config
from fjord.feedback import models


def happy_redirect(request):
    # TODO: Remove this when the addon gets fixed and is pointing to
    # the correct urls.
    return HttpResponseRedirect(reverse('feedback') + '#happy')


def sad_redirect(request):
    # TODO: Remove this when the addon gets fixed and is pointing to
    # the correct urls.
    return HttpResponseRedirect(reverse('feedback') + '#sad')


@mobile_template('feedback/{mobile/}download_firefox.html')
def download_firefox(request, template):
    return render(request, template)


@mobile_template('feedback/{mobile/}thanks.html')
def thanks(request, template):
    return render(request, template)


def requires_firefox(func):
    """Redirects to "download firefox" page if not Firefox.

    If it isn't a Firefox browser, then we don't want to deal with it.

    This is a temporary solution. See bug #848568.

    """
    @wraps(func)
    def _requires_firefox(request, *args, **kwargs):
        # Note: This is sort of a lie. What's going on here is that
        # parse_ua only parses Firefox-y browsers. So if it's UNKNOWN
        # at this point, then it's not Firefox-y. If parse_ua ever
        # changes, then this will cease to be true.
        if request.BROWSER.browser == UNKNOWN:
            return HttpResponseRedirect(reverse('download-firefox'))
        return func(request, *args, **kwargs)
    return _requires_firefox


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

            # Inferred data from user agent
            prodchan=_get_prodchan(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            browser=request.BROWSER.browser,
            browser_version=request.BROWSER.browser_version,
            platform=platform,

            # Data that comes form the user or is inferred
            locale=data.get('locale', request.locale),

            # Data from mobile devices
            manufacturer=data.get('manufacturer', ''),
            device=data.get('device', ''),
        )

        # This data is coming from the web form where we infer many
        # things from the user agent. If the user agent is bogus, then
        # the browser is UNKNOWN. If that's the case, then we can't
        # infer anything useful for product, channel or version so we
        # set them to empty strings.
        if opinion.browser == UNKNOWN:
            opinion.product = u''
            opinion.channel = u''
            opinion.version = u''

        else:
            opinion.product = data.get(
                'product', models.Response.infer_product(platform))
            # For now, we assume everything is stable because we don't
            # know otherwise.
            opinion.channel = u'stable'
            opinion.version = data.get(
                'version', request.BROWSER.browser_version)

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
    elif meta.platform == 'Firefox OS':
        platform = 'fxos'
    elif product == 'firefox':
        platform = 'desktop'
    else:
        platform = 'unknown'

    return '{0}.{1}.{2}'.format(product, platform, channel)


@requires_firefox
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


@requires_firefox
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


@requires_firefox
def firefox_os_stable_feedback(request):
    return render(request, 'feedback/mobile/fxos_feedback.html', {
        'countries': config.FIREFOX_OS_COUNTRIES,
        'devices': config.FIREFOX_OS_DEVICES,
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

    # Make `request.POST` mutable.
    request.POST = request.POST.copy()

    # For _type, 1 is happy, 2 is sad, 3 is idea. We convert that so
    # that _type = 1 -> happy = 1 and everything else -> happy = 0.
    if request.POST.get('_type') == '1':
        happy = 1
    else:
        happy = 0
    request.POST['happy'] = happy

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
    'firefox.fxos.stable': firefox_os_stable_feedback,
}


@csrf_exempt
@never_cache
def feedback_router(request, formname=None, *args, **kwargs):
    """Determine a view to use, and call it.

    If formname is given, reference `feedback_routes` to look up a view.
    If `formname` is not passed, or isn't found in `feedback_routes`,
    asssume the user is either a stable desktop Firefox or a stable
    mobile Firefox based on the parsed UA, and serve them the appropriate
    page.

    Note: We never want to cache this view.
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
        if request.BROWSER.browser == 'Firefox OS':
            view = firefox_os_stable_feedback
        elif request.BROWSER.mobile:
            view = mobile_stable_feedback
        else:
            view = desktop_stable_feedback

    return view(request, *args, **kwargs)


class PostFeedbackAPI(generics.CreateAPIView):
    serializer_class = models.ResponseSerializer
