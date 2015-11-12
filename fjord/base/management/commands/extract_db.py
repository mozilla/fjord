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

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--outputfile',
            type=str,
            action='store',
            default=os.path.join(settings.BASE_DIR, 'fjord', 'base',
                                 'db_strings.py'),
            help=(
                'The file where extracted strings are written to. (Default: '
                '%default)'
            ),
        )

    def handle(self, *args, **options):
        try:
            apps = settings.DB_LOCALIZE
        except AttributeError:
            raise CommandError('DB_LOCALIZE setting is not defined!')

        outputfile = options['outputfile']

        strings = []
        for app, models in apps.items():
            for model, params in models.items():
                model_class = get_model(app, model)
                attrs = params['attrs']
                qs_fun = params.get('queryset', lambda cls: cls.objects.all())
                qs = qs_fun(model_class).values_list(*attrs).distinct()
                for item in qs:
                    for i in range(len(attrs)):
                        msg = {
                            'id': item[i],
                            'loc': 'DB: %s.%s.%s' % (app, model, attrs[i]),
                            'comments': params.get('comments')
                        }
                        strings.append(msg)

        py_file = os.path.expanduser(outputfile)
        py_file = os.path.abspath(py_file)

        print 'Outputting db strings to: %s' % py_file
        with open(py_file, 'w+') as f:
            f.write(HEADER)
            f.write(
                'from django.utils.translation import ugettext_lazy as _lazy'
                '\n\n'
            )
            for s in strings:
                comments = s['comments']
                if comments:
                    for c in comments:
                        f.write((u'# l10n: %s\n' % c).encode('utf8'))

                f.write(
                    (u'_lazy("""%(id)s""", \'%(loc)s\')\n' % s).encode('utf8')
                )
