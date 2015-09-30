# NOTE: This code was copied from tower.
# TODO: Look into switching to makemessages provided by django-jinja.
import os
import tempfile
from subprocess import Popen

from django.core.management.base import BaseCommand
from django.conf import settings

from babel.messages.extract import DEFAULT_KEYWORDS, extract_from_dir
from translate.storage import po

from fjord.base.l10n import split_context


DEFAULT_DOMAIN = 'all'
TEXT_DOMAIN = 'django'
KEYWORDS = dict(DEFAULT_KEYWORDS)
KEYWORDS['_lazy'] = None

# List of domains that should be separate from the django.pot file.
STANDALONE_DOMAINS = [TEXT_DOMAIN]

OPTIONS_MAP = {
    '**.*': {
        # Get list of extensions for django-jinja template backend
        'extensions': ','.join(settings.TEMPLATES[0]['OPTIONS']['extensions'])
    }
}

COMMENT_TAGS = ['L10n:', 'L10N:', 'l10n:', 'l10N:']


def create_pounit(filename, lineno, message, comments):
    unit = po.pounit(encoding='UTF-8')
    context, msgid = split_context(message)
    unit.setsource(msgid)
    if context:
        unit.msgctxt = ['"%s"' % context]
    for comment in comments:
        unit.addnote(comment, 'developer')

    unit.addlocation('%s:%s' % (filename, lineno))
    return unit


def create_pofile_from_babel(extracted):
    catalog = po.pofile()

    for extracted_unit in extracted:
        filename, lineno, message, comments, context = extracted_unit
        unit = create_pounit(filename, lineno, message, comments)
        catalog.addunit(unit)

    catalog.removeduplicates()
    return catalog


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--domain', '-d', default=DEFAULT_DOMAIN, dest='domain',
            help=(
                'The domain of the message files.  If "all" '
                'everything will be extracted and combined into '
                '%s.pot. (default: %%default).' % TEXT_DOMAIN
            )
        )
        parser.add_argument(
            '--output-dir', '-o',
            default=os.path.join(settings.ROOT, 'locale', 'templates',
                                 'LC_MESSAGES'),
            dest='outputdir',
            help=(
                'The directory where extracted files will be placed. '
                '(Default: %default)'
            )
        )
        parser.add_argument(
            '-c', '--create',
            action='store_true', dest='create', default=False,
            help='Create output-dir if missing'
        )

    def handle(self, *args, **options):
        domains = options.get('domain')
        outputdir = os.path.abspath(options.get('outputdir'))

        if not os.path.isdir(outputdir):
            if not options.get('create'):
                print ('Output directory must exist (%s) unless -c option is '
                       'given. Specify one with --output-dir' % outputdir)
                return 'FAILURE\n'

            os.makedirs(outputdir)

        if domains == 'all':
            domains = settings.DOMAIN_METHODS.keys()
        else:
            domains = [domains]

        root = settings.ROOT

        def callback(filename, method, options):
            if method != 'ignore':
                print '  %s' % filename

        for domain in domains:
            print 'Extracting all strings in domain %s...' % (domain)

            methods = settings.DOMAIN_METHODS[domain]
            extracted = extract_from_dir(
                root,
                method_map=methods,
                keywords=KEYWORDS,
                comment_tags=COMMENT_TAGS,
                callback=callback,
                options_map=OPTIONS_MAP,
            )
            catalog = create_pofile_from_babel(extracted)
            if not os.path.exists(outputdir):
                raise Exception('Expected %s to exist... BAILING' % outputdir)

            catalog.savefile(os.path.join(outputdir, '%s.pot' % domain))

        pot_files = []
        for i in [x for x in domains if x not in STANDALONE_DOMAINS]:
            pot_files.append(os.path.join(outputdir, '%s.pot' % i))

        if len(pot_files) > 1:
            print ('Concatenating the non-standalone domains into %s.pot' %
                   TEXT_DOMAIN)

            final_out = os.path.join(outputdir, '%s.pot' % TEXT_DOMAIN)

            # We add final_out back on because msgcat will combine all
            # specified files.  We'll redirect everything back in to
            # final_out in a minute.
            pot_files.append(final_out)

            meltingpot = tempfile.TemporaryFile()
            p1 = Popen(['msgcat'] + pot_files, stdout=meltingpot)
            p1.communicate()
            meltingpot.seek(0)

            # w+ truncates the file first
            with open(final_out, 'w+') as final:
                final.write(meltingpot.read())

            meltingpot.close()

            for i in [x for x in domains if x not in STANDALONE_DOMAINS]:
                os.remove(os.path.join(outputdir, '%s.pot' % i))

        print 'Done'
