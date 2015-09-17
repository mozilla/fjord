from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Converts specified user into a superuser'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs=1,
                            help='Email address for account to elevate.')

    def handle(self, *args, **options):
        email = options['email'][0]

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            raise CommandError('User %s does not exist.' % email)

        if user.is_superuser and user.is_staff:
            raise CommandError('User already has the power!')

        user.is_superuser = True
        user.is_staff = True
        user.save()
        print 'Done!'
