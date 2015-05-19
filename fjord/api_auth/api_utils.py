from django.contrib.auth.models import AnonymousUser

from rest_framework import authentication
from rest_framework import exceptions

from fjord.api_auth.models import Token


class TokenAuthentication(authentication.BaseAuthentication):
    """Authenticates against a api_auth Token. This is loosely based on
    the django-rest-framework TokenAuthentication except theirs is
    tied to Django users.

    """
    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth:
            # FIXME: ZLB isn't passing along the Authorization header,
            # so we never see it in Django land. This adds support for
            # an additional header. Why support an additional one?
            # Because when we switch to AWS, we can alleviate this
            # silliness.
            auth = request.META.get('HTTP_FJORD_AUTHORIZATION', '')

        auth = auth.split()

        if not auth or auth[0].lower() != 'token':
            # Return None so that other authentication schemes can see
            # if they handle this.
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed(
                'Invalid token header. No token provided.'
            )

        if len(auth) > 2:
            raise exceptions.AuthenticationFailed(
                'Invalid token header. Token string should not contain spaces.'
            )

        try:
            token = Token.objects.get(token=auth[1])
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token.')

        if not token.enabled:
            raise exceptions.AuthenticationFailed('Token disabled.')

        # These tokens are user-agnostic. DRF3 assignes the user to
        # request.user and if that's None, then middleware can fail.
        # Instead we pass AnonymousUser.
        return (AnonymousUser(), token)

    def authenticate_header(self, request):
        return 'Token'
