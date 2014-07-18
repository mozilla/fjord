from functools import wraps

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from mobility.decorators import mobile_template
from statsd import statsd

from fjord.base.browsers import UNKNOWN
from fjord.base.urlresolvers import reverse
from fjord.base.util import (
    smart_str,
    translate_country_name
)
from fjord.feedback import config
from fjord.feedback import models
from fjord.feedback.forms import ResponseForm
from fjord.feedback.utils import actual_ip_plus_desc, clean_url, ratelimit


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


@ratelimit(rulename='doublesubmit_1pm', keyfun=actual_ip_plus_desc, rate='1/m')
@ratelimit(rulename='100ph', rate='100/h')
def _handle_feedback_post(request, locale=None, product=None,
                          version=None, channel=None):
    """Saves feedback post to db accounting for throttling

    :arg request: request we're handling the post for
    :arg locale: locale specified in the url
    :arg product: validated and sanitized product slug specified in
        the url
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

    data = form.cleaned_data
    description = data.get('description', u'').strip()
    if not description:
        # If there's no description, then there's nothing to do here,
        # so thank the user and move on.
        return HttpResponseRedirect(reverse('thanks'))

    # Do some data validation of product, channel and version
    # coming from the url.
    if product:
        # If there was a product in the url, that's a product slug, so
        # we map it to a db_name which is what we want to save to the
        # db.
        product = models.Product.get_product_map()[product]

    # src, then source, then utm_source
    source = request.GET.get('src', u'')
    if not source:
        source = request.GET.get('utm_source', u'')

    campaign = request.GET.get('utm_campaign', u'')

    # If the product came in on the url, then we only want to populate
    # the platfrom from the user agent data iff the product specified
    # by the url is the same as the browser product.
    platform = u''
    if product is None or product == request.BROWSER.browser:
        # Most platforms aren't different enough between versions to care.
        # Windows is.
        platform = request.BROWSER.platform
        if platform == 'Windows':
            platform += ' ' + request.BROWSER.platform_version

    product = product or u''

    opinion = models.Response(
        # Data coming from the user
        happy=data['happy'],
        url=clean_url(data.get('url', u'')),
        description=data['description'].strip(),

        # Inferred data from user agent
        prodchan=_get_prodchan(request, product, channel),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        browser=request.BROWSER.browser,
        browser_version=request.BROWSER.browser_version,
        platform=platform,

        # Pulled from the form data or the url
        locale=data.get('locale', locale),

        # Data from mobile devices which is probably only
        # applicable to mobile devices
        manufacturer=data.get('manufacturer', ''),
        device=data.get('device', ''),
    )

    if source:
        opinion.source = source[:100]

    if campaign:
        opinion.campaign = campaign[:100]

    if product:
        # If we picked up the product from the url, we use url
        # bits for everything.
        product = product or u''
        version = version or u''
        channel = channel or u''

    elif opinion.browser != UNKNOWN:
        # If we didn't pick up a product from the url, then we
        # infer as much as we can from the user agent.
        product = data.get(
            'product', models.Response.infer_product(platform))
        version = data.get(
            'version', request.BROWSER.browser_version)
        # Assume everything we don't know about is stable channel.
        channel = u'stable'

    else:
        product = channel = version = u''

    opinion.product = product or u''
    opinion.version = version or u''
    opinion.channel = channel or u''

    opinion.save()

    # If there was an email address, save that separately.
    if data.get('email_ok') and data.get('email'):
        e = models.ResponseEmail(email=data['email'], opinion=opinion)
        e.save()

    if data['happy']:
        statsd.incr('feedback.happy')
    else:
        statsd.incr('feedback.sad')

    return HttpResponseRedirect(reverse('thanks'))


def _get_prodchan(request, product=None, channel=None):
    # FIXME - redo this to handle product/channel
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
    })


@csrf_protect
def generic_feedback_dev(request, locale, product, version=None, channel=None):
    """IN DEVELOPMENT NEXT GENERATION GENERIC FEEDBACK FORM"""
    form = ResponseForm()

    if request.method == 'POST':
        return _handle_feedback_post(request, locale, product,
                                     version, channel)

    return render(request, 'feedback/generic_feedback_dev.html', {
        'form': form,
        'product': models.Product.from_slug(product),
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
    'genericdev': generic_feedback_dev,
}


@csrf_exempt
@never_cache
def feedback_router_dev(request, product=None, version=None, channel=None,
                    *args, **kwargs):
    """DEV ONLY FEEDBACK ROUTER"""
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

        # This lets us measure how often this section of code kicks
        # off and thus how often old android stuff is happening. When
        # we're not seeing this anymore, we can nix all the old
        # android stuff.
        statsd.incr('feedback.oldandroid')

        return android_about_feedback(request, request.locale)

    product = smart_str(product, fallback=None)
    # FIXME - validate these better
    version = smart_str(version)
    channel = smart_str(channel).lower()

    if product == 'fxos' or request.BROWSER.browser == 'Firefox OS':
        # Firefox OS gets shunted to a different form which has
        # different Firefox OS specific questions.
        view = firefox_os_stable_feedback
        product = 'fxos'

    elif product in PRODUCT_OVERRIDE:
        # The "product" is really a specific form to use. So we None
        # out the product and let that form view deal with everything.
        view = PRODUCT_OVERRIDE[product]
        product = None

    elif product is None or product not in models.Product.get_product_map():
        # The product wasn't specified or doesn't exist, so we spit
        # out the product picker.
        template = 'feedback/picker.html'

        products = models.Product.objects.all()
        return render(request, template, {
            'products': products
        })

    view = view or generic_feedback_dev
        
    return view(request, request.locale, product, version, channel,
                *args, **kwargs)


@csrf_exempt
@never_cache
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
    version = smart_str(version)
    channel = smart_str(channel).lower()

    if product == 'fxos' or request.BROWSER.browser == 'Firefox OS':
        # Firefox OS gets shunted to a different form which has
        # different Firefox OS specific questions.
        view = firefox_os_stable_feedback
        product = 'fxos'

    elif product:
        product = smart_str(product)

        if product in PRODUCT_OVERRIDE:
            # If the product is really a form name, we use that
            # form specifically.
            view = PRODUCT_OVERRIDE[product]
            product = None

        elif product not in models.Product.get_product_map():
            # If they passed in a product and we don't know about
            # it, stop here.
            return render(request, 'feedback/unknownproduct.html', {
                'product': product
            })

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
