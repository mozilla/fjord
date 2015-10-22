# NOTE: This code was copied from tower.
import os
import tempfile
from subprocess import Popen

from django.core.management.base import BaseCommand
from django.conf import settings

from babel.messages.extract import DEFAULT_KEYWORDS, extract_from_dir
from translate.storage import po

# FIXME: Move settings handling into a settings module

# FIXME: Put all the settings under TOWER as a dict
DEFAULT_DOMAIN = 'all'
TEXT_DOMAIN = 'django'

# FIXME: Make this configurable and default it to babel defaults plus
# Django _lazy variants
KEYWORDS = dict(DEFAULT_KEYWORDS)
KEYWORDS['_lazy'] = None

# Reinstitute DOMAINS settings, but default to just 'django'.
# List of domains that should be separate from the django.pot file.
STANDALONE_DOMAINS = [TEXT_DOMAIN]

OPTIONS_MAP = {
    '**.*': {
        # Get list of extensions for django-jinja template backend
        'extensions': ','.join(settings.TEMPLATES[0]['OPTIONS']['extensions'])
    }
}

COMMENT_TAGS = ['L10n:', 'L10N:', 'l10n:', 'l10N:']


def create_pounit(filename, lineno, msgid, comments, context):
    # FIXME: Test context handling
    unit = po.pounit(encoding='UTF-8')
    unit.setsource(msgid)
    if context:
        unit.msgctxt = ['"%s"' % context]
    for comment in comments:
        unit.addnote(comment, 'developer')

    unit.addlocation('%s:%s' % (filename, lineno))
    # FIXME: Add variable format flags
    # if python-format:
    #     unit.settypecomment('python-format', present=True)
    # if python-brace-format:
    #     unit.settypecomment('python-brace-format', present=True)
    return unit


def create_pofile_from_babel(extracted):
    catalog = po.pofile()

    for extracted_unit in extracted:
        filename, lineno, message, comments, context = extracted_unit
        unit = create_pounit(filename, lineno, message, comments, context)
        catalog.addunit(unit)

    catalog.removeduplicates()
    return catalog


def monkeypatch_i18n():
    """Alleviates problems with extraction for trans blocks

    Jinja2 has a ``babel_extract`` function which sets up a Jinja2
    environment to parse Jinja2 templates to extract strings for
    translation. That's awesome! Yay! However, when it goes to
    set up the environment, it checks to see if the environment
    has InternationalizationExtension in it and if not, adds it.

    https://github.com/mitsuhiko/jinja2/blob/2.8/jinja2/ext.py#L587

    That stomps on our TowerI18nExtension so trans blocks don't get
    whitespace collapsed and we end up with msgids that are different
    between extraction and rendering. Argh!

    Two possible ways to deal with this:

    1. Rename our block from "trans" to something else like
       "blocktrans" or "transam".

       This means everyone has to make sweeping changes to their
       templates plus we adjust gettext, too, so now we're talking
       about two different extensions.

    2. Have people include both InternationalizationExtension
       before TowerI18nExtension even though it gets stomped on.

       This will look wrong in settings and someone will want to
       "fix" it thus breaking extractino subtly, so I'm loathe to
       force everyone to do this.

    3. Stomp on the InternationalizationExtension variable in
       ``jinja2.ext`` just before message extraction.

       This is easy and hopefully the underlying issue will go away
       soon.


    For now, we're going to do number 3. Why? Because I'm hoping
    Jinja2 will fix the trans tag so it collapses whitespace if
    you tell it to. Then we don't have to do what we're doing and
    all these problems go away.

    We can remove this monkeypatch when one of the following is true:

    1. we remove our whitespace collapsing code because Jinja2 trans
       tag supports whitespace collapsing
    2. Jinja2's ``babel_extract`` stops adding
       InternationalizationExtension to the environment if it's
       not there

    """
    import jinja2.ext
    from fjord.l10n.ext import TowerI18nExtension

    jinja2.ext.InternationalizationExtension = TowerI18nExtension
    jinja2.ext.i18n = TowerI18nExtension


class Command(BaseCommand):
    help = 'Extracts strings for translation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain', '-d', default=DEFAULT_DOMAIN, dest='domain',
            help=(
                'The domain of the message files.  If "all" '
                'everything will be extracted and combined into '
                '%s.pot. (default: %%%%default).' % TEXT_DOMAIN
            )
        )
        parser.add_argument(
            '--output-dir', '-o',
            default=os.path.join(settings.ROOT, 'locale', 'templates',
                                 'LC_MESSAGES'),
            dest='outputdir',
            help=(
                'The directory where extracted files will be placed. '
                '(Default: %%default)'
            )
        )
        parser.add_argument(
            '-c', '--create',
            action='store_true', dest='create', default=False,
            help='Create output-dir if missing'
        )

    def handle(self, *args, **options):
        # Must monkeypatch first to fix InternationalizationExtension
        # stomping issues! See docstring for details.
        monkeypatch_i18n()

        domains = options.get('domain')
        outputdir = os.path.abspath(options.get('outputdir'))

        if not os.path.isdir(outputdir):
            if not options.get('create'):
                print ('Output directory must exist (%s) unless -c option is '
                       'given. Specify one with --output-dir' % outputdir)
                # FIXME: This should return a non-zero exit code and
                # print to stderr however that works in Django.
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
                # FIXME: This should return a non-zero exit code and
                # print to stderr and be consistent
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
