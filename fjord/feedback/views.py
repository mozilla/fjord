import json
from functools import wraps

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from statsd.defaults.django import statsd
import waffle

from fjord.base.browsers import UNKNOWN
from fjord.base.urlresolvers import reverse
from fjord.base.utils import (
    actual_ip_plus_context,
    ratelimit,
    smart_int,
    smart_str,
    translate_country_name
)
from fjord.feedback import config
from fjord.feedback import models
from fjord.feedback.forms import ResponseForm
from fjord.feedback.models import Product, Response
from fjord.feedback.utils import clean_url
from fjord.feedback.config import TRUNCATE_LENGTH
from fjord.suggest.utils import get_suggestions


# Feedback configurations for products. If it's not in here, you'll get
# the generic one.
#
# product_slug -> {'view': view_fun, 'thanks_template': template_path}
PRODUCT_CONFIG = {}


def register_feedback_config(product_slug, thanks_template):
    """Registers a product config

    Example::

        @register_feedback_config('android', 'feedback/android_thanks.html')
        @csrf_protect
        def android_feedback(request, locale=None, product=None, version=None,
                             channel=None):
            # blah blah blah

    """
    def _register(fun):
        PRODUCT_CONFIG[product_slug] = {
            'view': fun,
            'thanks_template': thanks_template
        }
        return fun
    return _register


def get_config(product_slug):
    """Returns a product config or the generic one"""
    return PRODUCT_CONFIG.get(product_slug, PRODUCT_CONFIG['generic'])


def happy_redirect(request):
    """Support older redirects from Input v1 era"""
    return HttpResponseRedirect(reverse('picker') + '?happy=1')


def sad_redirect(request):
    """Support older redirects from Input v1 era"""
    return HttpResponseRedirect(reverse('picker') + '?happy=0')


def thanks_view(request):
    feedback = None
    suggestions = None

    response_id = None
    # If the user is an analyzer/admin, then we let them specify
    # the response_id via the querystring. This makes debugging
    # the system easier.
    if ((request.user.is_authenticated()
         and request.user.has_perm('analytics.can_view_dashboard'))):
        response_id = smart_int(request.GET.get('response_id', None))

    # If we don't have a response_id, then pull it from the
    # session where it was placed if the user had just left
    # feedback.
    if not response_id:
        response_id = request.session.get('response_id')

    if response_id:
        try:
            feedback = Response.objects.get(id=response_id)
        except Response.DoesNotExist:
            pass

    if feedback:
        product = Product.objects.get(db_name=feedback.product)
        suggestions = get_suggestions(feedback, request)
    else:
        # If there's no feedback, then we just show the thanks page as if it
        # were for Firefox. This is a weird edge case that might happen if the
        # user has cookies disabled or something like that.
        product = Product.objects.get(db_name=u'Firefox')

    template = get_config(product.slug)['thanks_template']

    return render(request, template, {
        'product': product,
        'feedback': feedback,
        'suggestions': suggestions
    })


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
        url=clean_url(data.get('url', u'').strip()),
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

        opinion.browser = browser.browser[:30]
        opinion.browser_version = browser.browser_version[:30]
        bp = browser.platform
        if bp == 'Windows':
            bp += (' ' + browser.platform_version)
        opinion.browser_platform = bp[:30]
        opinion.user_agent = user_agent[:config.USER_AGENT_LENGTH]

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

    # If they sent "happy=1"/"happy=0" in the querystring, it will get
    # picked up by the javascript in the form and we can just drop it
    # here.
    get_data.pop('happy', None)

    platform = u''

    if product:
        # If we have a product at this point, then it came from the
        # url and it's a Product instance and we need to turn it into
        # the product.db_name which is a string.
        product_db_name = product.db_name
    else:
        # Check the POST data for the product.
        product_db_name = data.get('product', '')

    # For the version, we try the url data, then the POST data.
    version = version or data.get('version', '')

    # At this point, we have a bunch of values, but we might be
    # missing some values, too. We're going to cautiously infer data
    # from the user agent where we're very confident it's appropriate
    # to do so.
    if request.BROWSER != UNKNOWN:
        # If we don't have a product, try to infer that from the user
        # agent information.
        if not product_db_name:
            product_db_name = models.Response.infer_product(request.BROWSER)

        # If we have a product and it matches the user agent browser,
        # then we can infer the version and platform from the user
        # agent if they're missing.
        if product_db_name:
            product = models.Product.objects.get(db_name=product_db_name)
            if product.browser and product.browser == request.BROWSER.browser:
                if not version:
                    version = request.BROWSER.browser_version
                if not platform:
                    platform = models.Response.infer_platform(
                        product_db_name, request.BROWSER)

    # Make sure values are at least empty strings--no Nones.
    opinion.product = (product_db_name or u'')[:30]
    opinion.version = (version or u'')[:30]
    opinion.channel = (channel or u'')[:30]
    opinion.platform = (platform or u'')[:30]

    opinion.save()

    # If there was an email address, save that separately.
    if data.get('email_ok') and data.get('email'):
        e = models.ResponseEmail(email=data['email'], opinion=opinion)
        e.save()
        statsd.incr('feedback.emaildata.optin')

    # If there's browser data, save that separately.
    if data.get('browser_ok'):
        # This comes in as a JSON string. Because we're using
        # JSONObjectField, we need to convert it back to Python and
        # then save it. This is kind of silly, but it does guarantee
        # we have valid JSON.
        try:
            browser_data = data['browser_data']
            browser_data = json.loads(browser_data)

        except ValueError:
            # Handles empty string and any non-JSON value.
            statsd.incr('feedback.browserdata.badvalue')

        except KeyError:
            # Handles the case where it's missing from the data
            # dict. If it's missing, we don't want to do anything
            # including metrics.
            pass

        else:
            # If browser_data isn't an empty dict, then save it.
            if browser_data:
                rti = models.ResponsePI(
                    data=browser_data, opinion=opinion)
                rti.save()
                statsd.incr('feedback.browserdata.optin')

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
        statsd.incr('feedback.contextdata.optin')

    if data['happy']:
        statsd.incr('feedback.happy')
    else:
        statsd.incr('feedback.sad')

    request.session['response_id'] = opinion.id

    return HttpResponseRedirect(reverse('thanks'))


@register_feedback_config('generic', 'feedback/thanks.html')
@csrf_protect
def generic_feedback(request, locale=None, product=None, version=None,
                     channel=None):
    """Generic feedback form for desktop and mobile"""
    form = ResponseForm()

    if request.method == 'POST':
        return _handle_feedback_post(request, locale, product,
                                     version, channel)

    bd = product.collect_browser_data_for(request.BROWSER.browser)

    return render(request, 'feedback/generic_feedback.html', {
        'form': form,
        'product': product,
        'collect_browser_data': bd,
        'TRUNCATE_LENGTH': TRUNCATE_LENGTH,
    })


@register_feedback_config('fxos', None)
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
        'product': product
    })


def fix_oldandroid(request):
    """Fixes old android requests

    Old versions of Firefox for Android have an in-product feedback form that
    generates POSTS directly to Input and is always "sad" or "idea". The POST
    data matches what the old Input used to do. The new Input doesn't have a
    ``_type`` field and doesn't have "idea" feedback, so we switch "idea" to be
    "sad", put it in the right field and then additionally tag the feedback
    with a source if it doesn't already have one.

    FIXME: Measure usage of this and nix it when we can. See bug #964292.

    :arg request: a Request object

    :returns: a fixed Request object

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

    # If there's no source, then we tag it with a source so we can distinguish
    # these from other feedback and know when we can remove this code.
    if not ('src' in request.GET or 'utm_source' in request.GET):
        request.GET = request.GET.copy()
        request.GET['utm_source'] = 'oldfennec-in-product'

    statsd.incr('feedback.oldandroid')

    return request


def persist_feedbackdev(fun):
    """Persists a feedbackdev flag set via querystring in the cookies"""
    @wraps(fun)
    def _persist_feedbackdev(request, *args, **kwargs):
        qs_feedbackdev = request.GET.get('feedbackdev', None)
        resp = fun(request, *args, **kwargs)
        if resp is not None and qs_feedbackdev is not None:
            resp.set_cookie(
                waffle.get_setting('COOKIE') % 'feedbackdev',
                qs_feedbackdev)

        return resp
    return _persist_feedbackdev


@csrf_exempt  # Need for oldandroid feedback POST handling
def picker_view(request):
    """View showing the product picker"""
    # The old Firefox for Android would POST form data to /feedback/. If we see
    # that, we fix the request up and then handle it as a feedback post.
    if '_type' in request.POST:
        request = fix_oldandroid(request)
        return _handle_feedback_post(request, request.locale)

    picker_products = models.Product.objects.on_picker()
    return render(request, 'feedback/picker.html', {
        'products': picker_products
    })


@csrf_exempt
@never_cache
@persist_feedbackdev
def feedback_router(request, product_slug=None, version=None, channel=None,
                    *args, **kwargs):
    """Figure out which flow to use for a product and route accordingly

    .. Note::

       1. We never want to cache this view

       2. Pages returned from this view will get an::

              X-Frame-Options: DENY

          HTTP header. That's important because these pages have magic
          powers and should never be used in frames. Please do not
          change this!

    """
    # The old Firefox for Android would POST form data to /feedback/. If we see
    # that, we fix the request up and then handle it as a feedback post.
    if '_type' in request.POST:
        request = fix_oldandroid(request)
        return _handle_feedback_post(request, request.locale)

    # FIXME - validate these better
    product_slug = smart_str(product_slug, fallback=None)
    version = smart_str(version)
    channel = smart_str(channel).lower()

    view_fun = get_config(product_slug)['view']

    if product_slug not in models.Product.objects.get_product_map():
        # If the product doesn't exist, redirect them to the picker.
        return HttpResponseRedirect(reverse('picker'))

    # Convert the product_slug to a product and send them on their way.
    product = models.Product.objects.from_slug(product_slug)
    return view_fun(request, request.locale, product, version, channel,
                    *args, **kwargs)
