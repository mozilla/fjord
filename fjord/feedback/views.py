import json
from functools import wraps

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from mobility.decorators import mobile_template
from statsd import statsd
import waffle

from fjord.base.browsers import UNKNOWN
from fjord.base.urlresolvers import reverse
from fjord.base.utils import (
    actual_ip_plus_context,
    ratelimit,
    smart_str,
    translate_country_name
)
from fjord.feedback import config
from fjord.feedback import models
from fjord.feedback.forms import ResponseForm
from fjord.feedback.utils import clean_url
from fjord.feedback.config import TRUNCATE_LENGTH


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


def thanks(request):
    template = 'feedback/thanks.html'
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


@ratelimit(rulename='doublesubmit_1p10m',
           keyfun=actual_ip_plus_context(
               lambda req: req.POST.get('description', u'no description')),
           rate='1/10m')
@ratelimit(rulename='50ph', rate='50/h')
def _handle_feedback_post(request, locale=None, product=None,
                          version=None, channel=None):
    """Saves feedback post to db accounting for throttling

    :arg request: request we're handling the post for
    :arg locale: locale specified in the url
    :arg product: None or the Product
    :arg version: validated and sanitized version specified in the url
    :arg channel: validated and sanitized channel specified in the url

    """
    if getattr(request, 'limited', False):
        # If we're throttled, then return the thanks page, but don't
        # add the response to the db.
        return HttpResponseRedirect(reverse('thanks'))

    # Get the form and run is_valid() so it goes through the
    # validation and cleaning machinery. We don't really care if it's
    # valid, though, since we will take what we got and do the best we
    # can with it. Error validation is now in JS.
    form = ResponseForm(request.POST)
    form.is_valid()

    get_data = request.GET.copy()

    data = form.cleaned_data

    description = data.get('description', u'').strip()
    if not description:
        # If there's no description, then there's nothing to do here,
        # so thank the user and move on.
        return HttpResponseRedirect(reverse('thanks'))

    opinion = models.Response(
        # Data coming from the user
        happy=data['happy'],
        url=clean_url(data.get('url', u'')),
        description=description,

        # Pulled from the form data or the url
        locale=data.get('locale', locale),

        # Data from mobile devices which is probably only
        # applicable to mobile devices
        manufacturer=data.get('manufacturer', ''),
        device=data.get('device', ''),
    )

    # Add user_agent and inferred data.
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if user_agent:
        browser = request.BROWSER

        opinion.user_agent = user_agent
        opinion.browser = browser.browser
        opinion.browser_version = browser.browser_version
        opinion.browser_platform = browser.platform
        if browser.platform == 'Windows':
            opinion.browser_platform += ' ' + browser.platform_version

    # source is src or utm_source
    source = (
        get_data.pop('src', [u''])[0] or
        get_data.pop('utm_source', [u''])[0]
    )
    if source:
        opinion.source = source[:100]

    campaign = get_data.pop('utm_campaign', [u''])[0]
    if campaign:
        opinion.campaign = campaign[:100]

    platform = u''

    if product:
        # If we have a product at this point, then it came from the
        # url and it's a Product instance and we need to turn it into
        # the product.db_name which is a string.
        product = product.db_name
    else:
        # Check the POST data for the product.
        product = data.get('product', '')

    # For the version, we try the url data, then the POST data.
    version = version or data.get('version', '')

    # At this point, we have a bunch of values, but we might be
    # missing some values, too. We're going to cautiously infer data
    # from the user agent where we're very confident it's appropriate
    # to do so.
    if request.BROWSER != UNKNOWN:
        # If we don't have a product, try to infer that from the user
        # agent.
        if not product:
            product = models.Response.infer_product(request.BROWSER)

        # If we have a product and it matches the user agent product,
        # then we can infer the version and platform from the user
        # agent if they're missing.
        if (product and product == models.Response.infer_product(
                request.BROWSER)):
            if not version:
                version = request.BROWSER.browser_version
            if not platform:
                platform = models.Response.infer_platform(
                    product, request.BROWSER)

    # Make sure values are at least empty strings--no Nones.
    opinion.product = product or u''
    opinion.version = version or u''
    opinion.channel = channel or u''
    opinion.platform = platform or u''

    opinion.save()

    # If there was an email address, save that separately.
    if data.get('email_ok') and data.get('email'):
        e = models.ResponseEmail(email=data['email'], opinion=opinion)
        e.save()

    # If there's browser data, save that separately.
    if data.get('browser_ok') and data.get('browser_data'):
        # This comes in as a JSON string. Because we're using
        # JSONObjectField, we need to convert it back to Python and
        # then save it. This is kind of silly, but it does guarantee
        # we have valid JSON.
        try:
            browser_data = data['browser_data']
            browser_data = json.loads(browser_data)
            rti = models.ResponseTroubleshootingInfo(
                data=browser_data, opinion=opinion)
            rti.save()
            statsd.incr('feedback.browserdata.optin')
        except ValueError:
            statsd.incr('feedback.browserdata.badvalue')

    else:
        statsd.incr('feedback.browserdata.optout')

    if get_data:
        # There was extra context in the query string, so we grab that
        # with some restrictions and save it separately.
        slop = {}

        # We capture at most the first 20 key/val pairs
        get_data_items = sorted(get_data.items())[:20]

        for key, val in get_data_items:
            # Keys can be at most 20 characters long.
            key = key[:20]
            if len(val) == 1:
                val = val[0]

            # Values can be at most 20 characters long.
            val = val[:100]
            slop[key.encode('utf-8')] = val.encode('utf-8')

        context = models.ResponseContext(data=slop, opinion=opinion)
        context.save()

    if data['happy']:
        statsd.incr('feedback.happy')
    else:
        statsd.incr('feedback.sad')

    return HttpResponseRedirect(reverse('thanks'))


@csrf_protect
def generic_feedback(request, locale=None, product=None, version=None,
                     channel=None):
    """Generic feedback form for desktop and mobile"""
    form = ResponseForm()

    if request.method == 'POST':
        return _handle_feedback_post(request, locale, product,
                                     version, channel)

    return render(request, 'feedback/generic_feedback.html', {
        'form': form,
        'product': product,
        'TRUNCATE_LENGTH': TRUNCATE_LENGTH,
    })


@csrf_exempt
def firefox_os_stable_feedback(request, locale=None, product=None,
                               version=None, channel=None):
    # Localized country names are in region files in product
    # details. We try really hard to use localized country names, so
    # we use gettext and if that's not available, use whatever is in
    # product details.
    countries = [
        (code, translate_country_name(translation.get_language(),
                                      code, name, name_l10n))
        for code, name, name_l10n in config.FIREFOX_OS_COUNTRIES
    ]

    return render(request, 'feedback/fxos_feedback.html', {
        'countries': countries,
        'devices': config.FIREFOX_OS_DEVICES,
        'TRUNCATE_LENGTH': TRUNCATE_LENGTH,
    })


@csrf_exempt
@require_POST
def android_about_feedback(request, locale=None):
    """A view specifically for Firefox for Android.

    Firefox for Android has a feedback form built in that generates
    POSTS directly to Input, and is always sad or ideas. Since Input no
    longer supports idea feedbacks, everything is Sad.

    FIXME - measure usage of this and nix it when we can. See bug
    #964292.

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

    # Note: product, version and channel are always None in this view
    # since this is to handle backwards-compatibility. So we don't
    # bother passing them along.

    # We always return Thanks! now and ignore errors.
    return _handle_feedback_post(request, locale)


PRODUCT_OVERRIDE = {
}


def persist_feedbackdev(fun):
    """Persists a feedbackdev flag set via querystring in the cookies"""
    def _persist_feedbackdev(request, *args, **kwargs):
        qs_feedbackdev = request.GET.get('feedbackdev', None)
        resp = fun(request, *args, **kwargs)
        if resp is not None and qs_feedbackdev is not None:
            resp.set_cookie(waffle.COOKIE_NAME % 'feedbackdev', qs_feedbackdev)

        return resp
    return _persist_feedbackdev


@csrf_exempt
@never_cache
@persist_feedbackdev
def feedback_router(request, product=None, version=None, channel=None,
                    *args, **kwargs):
    """Determine a view to use, and call it.

    If product is given, reference `product_routes` to look up a view.
    If `product` is not passed, or isn't found in `product_routes`,
    asssume the user is either a stable desktop Firefox or a stable
    mobile Firefox based on the parsed UA, and serve them the
    appropriate page. This is to handle the old formname way of doing
    things. At some point P, we should measure usage of the old
    formnames and deprecate them.

    This also handles backwards-compatability with the old Firefox for
    Android form which can't have a CSRF token.

    Note: We never want to cache this view.

    """
    view = None

    if '_type' in request.POST:
        # Checks to see if `_type` is in the POST data and if so this
        # is coming from Firefox for Android which doesn't know
        # anything about csrf tokens. If that's the case, we send it
        # to a view specifically for FfA Otherwise we pass it to one
        # of the normal views, which enforces CSRF. Also, nix the
        # product just in case we're crossing the streams and
        # confusing new-style product urls with old-style backwards
        # compatability for the Android form.
        #
        # FIXME: Remove this hairbrained monstrosity when we don't need to
        # support the method that Firefox for Android currently uses to
        # post feedback which worked with the old input.mozilla.org.
        view = android_about_feedback
        product = None

        # This lets us measure how often this section of code kicks
        # off and thus how often old android stuff is happening. When
        # we're not seeing this anymore, we can nix all the old
        # android stuff.
        statsd.incr('feedback.oldandroid')

        return android_about_feedback(request, request.locale)

    # FIXME - validate these better
    product = smart_str(product, fallback=None)
    version = smart_str(version)
    channel = smart_str(channel).lower()

    if product == 'fxos' or request.BROWSER.browser == 'Firefox OS':
        # Firefox OS gets shunted to a different form which has
        # different Firefox OS specific questions.
        view = firefox_os_stable_feedback
        product = 'fxos'

    elif product in PRODUCT_OVERRIDE:
        # If the product is really a form name, we use that
        # form specifically.
        view = PRODUCT_OVERRIDE[product]
        product = None

    elif (product is None
          or product not in models.Product.get_product_map()):

        picker_products = models.Product.objects.filter(
            enabled=True, on_picker=True)
        return render(request, 'feedback/picker.html', {
            'products': picker_products
        })

    product = models.Product.from_slug(product)

    if view is None:
        view = generic_feedback

    return view(request, request.locale, product, version, channel,
                *args, **kwargs)


def cyoa(request):
    template = 'feedback/picker.html'

    products = models.Product.objects.all()
    return render(request, template, {
        'products': products
    })
