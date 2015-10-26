# NOTE: This code was copied from tower.
import os
import tempfile
from subprocess import Popen

from django.core.management.base import BaseCommand
from django.conf import settings

from babel.messages.extract import extract_from_dir
from translate.storage import po

from fjord.l10n.settings import get_setting


DEFAULT_DOMAIN_VALUE = 'all'


def generate_options_map():
    """Generate an ``options_map` to pass to ``extract_from_dir``

    This is the options_map that's used to generate a Jinja2 environment. We
    want to generate and environment for extraction that's the same as the
    environment we use for rendering.

    This allows developers to explicitly set a ``JINJA2_CONFIG`` in settings.
    If that's not there, then this will pull the relevant bits from the first
    Jinja2 backend listed in ``TEMPLATES``.

    """
    try:
        return settings.TOWER['JINJA2_CONFIG']
    except KeyError:
        pass

    for tmpl_config in settings.TEMPLATES:
        try:
            backend = tmpl_config['BACKEND']
        except KeyError:
            continue
        if backend == 'django_jinja.backend.Jinja2':
            config = {}
            for key in ('newstyle_gettext',
                        'autoescape',
                        'undefined',
                        'extensions'):
                try:
                    config[key] = tmpl_config[key]
                except KeyError:
                    pass
            return {'**.*': config}
    raise Exception('No valid jinja2 config found in settings.')


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
            '--domain', '-d', default=DEFAULT_DOMAIN_VALUE,
            dest='domain',
            help=(
                'The domain of the message files.  If "all" '
                'everything will be extracted and combined into '
                '%s.pot. (default: %%%%default).' % get_setting('TEXT_DOMAIN')
            )
        )
        parser.add_argument(
            '--output-dir', '-o',
            default=os.path.join(get_setting('ROOT'), 'locale', 'templates',
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

        # Get all the settings we need; we uppercase them so they're
        # obviously setings
        DOMAIN_METHODS = get_setting('DOMAIN_METHODS')
        STANDALONE_DOMAINS = get_setting('STANDALONE_DOMAINS')
        KEYWORDS = get_setting('KEYWORDS')
        COMMENT_TAGS = get_setting('COMMENT_TAGS')
        ROOT = get_setting('ROOT')

        keywords_dict = dict([(keyword, None) for keyword in KEYWORDS])

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

        if domains == DEFAULT_DOMAIN_VALUE:
            domains = DOMAIN_METHODS.keys()
        else:
            domains = [domains]

        def callback(filename, method, options):
            if method != 'ignore':
                print '  %s' % filename

        for domain in domains:
            print 'Extracting all strings in domain %s...' % (domain)

            methods = DOMAIN_METHODS[domain]
            extracted = extract_from_dir(
                ROOT,
                method_map=methods,
                keywords=keywords_dict,
                comment_tags=COMMENT_TAGS,
                callback=callback,
                options_map=generate_options_map(),
            )
            catalog = create_pofile_from_babel(extracted)
            if not os.path.exists(outputdir):
                # FIXME: This should return a non-zero exit code and
                # print to stderr and be consistent
                raise Exception('Expected %s to exist... BAILING' % outputdir)

            catalog.savefile(os.path.join(outputdir, '%s.pot' % domain))

        not_standalone_domains = [
            dom for dom in domains
            if dom not in STANDALONE_DOMAINS
        ]

        pot_files = []
        for dom in not_standalone_domains:
            pot_files.append(os.path.join(outputdir, '%s.pot' % dom))

        if len(pot_files) > 1:
            pot_file = get_setting('TEXT_DOMAIN') + '.pot'
            print ('Concatenating the non-standalone domains into %s' %
                   pot_file)

            final_out = os.path.join(outputdir, pot_file)

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

            for dom in not_standalone_domains:
                os.remove(os.path.join(outputdir, '%s.pot' % dom))

        print 'Done'
