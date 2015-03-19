from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from fjord.translations.models import get_translation_systems


class Command(BaseCommand):
    help = 'Translate some text with specified system.'
    option_list = BaseCommand.option_list + (
        make_option('--system', type='string', dest='system',
                    default=u'fake',
                    help=u'The translation system to use.'),
    )
    def handle(self, *args, **options):
        system = options['system']

        if len(args) < 2:
            raise CommandError(
                'Usage: ./manage.py trans [--system=SYSTEM] lang text'
            )

        lang, text = args

        system_classes = get_translation_systems().values()

        class TextClass(object):
            def __init__(self, src, locale):
                self.id = 'ou812'
                self.src = src
                self.locale = locale
                self.dest = ''

            def save(self, *args, **kwargs):
                pass

        instance = TextClass(text, lang)

        for system_cls in system_classes:
            if system_cls.name == system:
                system_cls().translate(instance, lang, 'src', 'en', 'dest')
                print 'Translated to:'
                print instance.dest
                break

        else:
             print 'No such translation system.'
             print ', '.join([system_cls.name for system_cls in system_classes])
