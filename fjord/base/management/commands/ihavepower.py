from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Converts specified user into a superuser'

    def handle(self, *args, **options):
        if not args:
            raise CommandError(
                'You must specify the account email address to elevate.')

        try:
            user = User.objects.get(email=args[0])

        except User.DoesNotExist:
            raise CommandError('User %s does not exist.' % args[0])

        if user.is_superuser and user.is_staff:
            raise CommandError('User already has the power!')

        user.is_superuser = True
        user.is_staff = True
        user.save()
        print 'Done!'
