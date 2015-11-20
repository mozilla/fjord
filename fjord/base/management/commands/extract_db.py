import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models.loading import get_model


HEADER = """\
#######################################################################
#
# Note: This file is a generated file--do not edit it directly!
# Instead make changes to the appropriate content in the database or
# write up a bug here:
#
#     https://bugzilla.mozilla.org/enter_bug.cgi?product=Input
#
# with the specific lines that are problematic and why.
#
# You can generate this file by running:
#
#     ./manage.py extract_db
#
#######################################################################
"""


class Command(BaseCommand):
    """
    Pulls strings from the database and puts them in a python file,
    wrapping each one in a gettext call.

    The models and attributes to pull are defined by DB_LOCALIZE:

    DB_LOCALIZE = {
        'some_app': {
            'SomeModel': {
                'attrs': ['attr_name', 'another_attr'],
            }
        },
        'another_app': {
            'AnotherModel': {
                'attrs': ['more_attrs'],
                'comments': ['Comment that will appear to localizers.'],
                'queryset': lambda cls: cls.objects.some_queryset()
            }
        },
    }

    Note: Database columns are expected to be CharFields or TextFields.

    """
    help = 'Pulls strings from the database and writes them to python file.'

    def handle(self, *args, **options):
        try:
            apps = settings.DB_LOCALIZE
        except AttributeError:
            raise CommandError('DB_LOCALIZE setting is not defined!')

        for app, models in apps.items():
            strings = []
            for model, params in models.items():
                model_class = get_model(app, model)
                attrs = params['attrs']
                qs_fun = params.get('queryset', lambda cls: cls.objects.all())
                qs = qs_fun(model_class).values_list(*attrs).distinct()
                for item in qs:
                    for i in range(len(attrs)):
                        msg = {
                            'id': item[i],
                            'ctxt': 'DB: %s.%s.%s' % (app, model, attrs[i]),
                            'comments': params.get('comments')
                        }
                        strings.append(msg)

            outputfile = os.path.join(
                settings.BASE_DIR, 'fjord', app, 'db_strings.py'
            )
            outputfile = os.path.abspath(outputfile)

            tmpl = u'pgettext("""%(ctxt)s""", """%(id)s""")\n'

            print 'Outputting db strings to: %s' % outputfile
            with open(outputfile, 'w+') as f:
                f.write(HEADER)
                f.write(
                    'from django.utils.translation import pgettext'
                    '\n\n'
                )
                for s in strings:
                    for c in s['comments']:
                        f.write((u'# l10n: %s\n' % c).encode('utf8'))

                    f.write((tmpl % s).encode('utf8'))
