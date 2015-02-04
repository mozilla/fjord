import ast
from urllib import urlencode

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render

from fjord.base.tests import LocalizingClient
from fjord.feedback.models import Product, Response


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'enabled',
        'on_dashboard',
        'on_picker',
        'display_name',
        'db_name',
        'translation_system',
        'browser_data_browser',
        'browser',
        'image_file',
        'notes',
        'slug')
    list_filter = ('enabled', 'on_dashboard', 'on_picker')


class EmptyFriendlyAVFLF(admin.AllValuesFieldListFilter):
    def choices(self, cl):
        """Displays empty string as <Empty>

        This makes it possible to choose Empty in the filter
        list. Otherwise empty strings display as '' and don't get any
        height and thus aren't selectable.

        """
        for choice in super(EmptyFriendlyAVFLF, self).choices(cl):
            if choice.get('display') == '':
                choice['display'] = '<Empty>'
            yield choice


class ResponseFeedbackAdmin(admin.ModelAdmin):
    list_display = ('created', 'product', 'channel', 'version', 'happy',
                    'description', 'user_agent', 'locale')
    list_filter = ('happy', ('product', EmptyFriendlyAVFLF),
                   ('locale', EmptyFriendlyAVFLF))
    search_fields = ('description',)
    actions = ['nix_product']
    list_per_page = 200

    def nix_product(self, request, queryset):
        ret = queryset.update(product=u'')
        self.message_user(request, '%s responses updated.' % ret)
    nix_product.short_description = u'Remove product for selected responses'


admin.site.register(Product, ProductAdmin)
admin.site.register(Response, ResponseFeedbackAdmin)


def parse_data(data):
    """Takes a string from a repr(WSGIRequest) and transliterates it

    This is incredibly gross "parsing" code that takes the WSGIRequest
    string from an error email and turns it into something that
    vaguely resembles the original WSGIRequest so that we can send
    it through the system again.

    """
    BEGIN = '<WSGIRequest'

    data = data.strip()
    data = data[data.find(BEGIN) + len(BEGIN):]
    if data.endswith('>'):
        data = data[:-1]

    container = {}
    key = ''
    for line in data.splitlines():
        # Lines that start with 'wsgi.' have values which are
        # objects. E.g. a logger. This won't fly with ast.literal_eval
        # so we just ignore all the wsgi. meta stuff.
        if not line or line.startswith(' \'wsgi.'):
            continue

        if line.startswith(' '):
            # If it starts with a space, then it's a continuation of
            # the current dict.
            container[key] += line
        else:
            key, val = line.split(':', 1)
            container[key.strip()] = val.strip()

    QUERYDICT = '<QueryDict: '

    for key, val in container.items():
        val = val.strip(',')

        if val.startswith(QUERYDICT):
            # GET and POST are both QueryDicts, so we nix the
            # QueryDict part and pretend they're regular dicts.
            #
            # <QueryDict: {...}> -> {...}
            val = val[len(QUERYDICT):-1]
        elif val.startswith('{'):
            # Regular dict that might be missing a } because we
            # dropped it when we were weeding out wsgi. lines.
            #
            # {... -> {...}
            val = val.strip()
            if not val.endswith('}'):
                val = val + '}'
        else:
            # This needs to have the string ornamentation added so it
            # literal_evals into a string.
            val = 'u"' + val + '"'

        # Note: We use ast.literal_eval here so that we're guaranteed
        # only to be getting out strings, lists, tuples, dicts,
        # booleans or None and not executing arbitrary Python code.
        val = ast.literal_eval(val)
        container[key] = val

    return container


def generate_response(response_data):
    """Takes a response data dict and generates a Response

    This (ab)uses the LocalizingClient to do the work so that it goes
    through all the existing view code which means I don't have to
    duplicate all that stuff here.

    """
    client = LocalizingClient(enforce_csrf_checks=False)

    url = response_data['path']
    if response_data['GET']:
        url = url + '?' + urlencode(response_data['GET'])

    # FIXME: Setting the HTTP_HOST to what was in the error works fine
    # in prod and in my development environment (which has
    # DEBUG=True), but it probably doesn't work on the -dev or -stage
    # environments.
    #
    # We can derive it from SITE_URL, but not all environments have
    # SITE_URL.
    #
    # Need to figure out a better way to do this.
    http_host = response_data['META']['HTTP_HOST']

    resp = client.post(
        url,
        data=response_data['POST'],
        HTTP_USER_AGENT=response_data['META']['HTTP_USER_AGENT'],
        HTTP_HOST=http_host
    )
    return resp


def response_entry_view(request):
    """OMG! THIS IS A CRAZY VIEW FOR CREATING RESPONSES FROM ERROR EMAILS!

    DON'T LOOK! ABANDON ALL HOPE ALL WHO ENTER HERE!

    This is an admin view so that we don't embarrass ourselves by
    showing what we've done to others.

    """
    if request.method == 'POST':
        data = request.POST['data']
        if '<WSGIRequest' in data:
            parsed_data = parse_data(data)
            desc = parsed_data['POST']['description'][0]
            resp = generate_response(parsed_data)
            if resp.status_code in (200, 302):
                feedback = (Response.objects
                            .filter(description=desc)
                            .latest('id'))
                messages.success(request, 'Created id %s' % feedback.id)

                return HttpResponseRedirect(request.path)
            else:
                messages.error(request, 'Raised: ' + str(resp.status_code))
        else:
            messages.error(
                request,
                'Cannot find "<WSGIRequest" in data. Try copy-and-pasting '
                'again.')

    return render(request, 'admin/response_entry.html')


admin.site.register_view(path='response-entry-view',
                         name='Response Entry',
                         view=response_entry_view)
