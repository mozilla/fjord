from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import serializers
import rest_framework.response
import rest_framework.views

from fjord.alerts.models import Alert, AlertFlavor, AlertSerializer, Link
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

        return (None, token)

    def authenticate_header(self, request):
        return 'Token'


class FlavorPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Is this token permitted to GET/POST alerts for this flavor?
        token = request.auth

        return token and obj.is_permitted(token)


def positive_integer(value):
    if value <= 0:
        raise serializers.ValidationError(
            'This field must be positive and non-zero.')


def is_after(value1, value2):
    return value1 and value2 and value1 > value2


class AlertsGETSerializer(serializers.Serializer):
    flavors = serializers.CharField(required=True)
    max = serializers.IntegerField(
        required=False, default=100,
        validators=[positive_integer])
    start_time_start = serializers.DateTimeField(required=False)
    start_time_end = serializers.DateTimeField(required=False)

    end_time_start = serializers.DateTimeField(required=False)
    end_time_end = serializers.DateTimeField(required=False)

    created_start = serializers.DateTimeField(required=False)
    created_end = serializers.DateTimeField(required=False)

    def validate(self, data):
        if is_after(data.get('start_time_start'), data.get('start_time_end')):
            raise serializers.ValidationError(
                'start_time_start must occur before start_time_end.')

        if is_after(data.get('end_time_start'), data.get('end_time_end')):
            raise serializers.ValidationError(
                'end_time_start must occur before end_time_end.')

        if is_after(data.get('created_start'), data.get('created_end')):
            raise serializers.ValidationError(
                'created_start must occur before created_end.')

        return data


class AlertsAPI(rest_framework.views.APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (FlavorPermission,)

    def rest_error(self, status, errors):
        return rest_framework.response.Response(
            status=status,
            data={
                'detail': errors
            })

    def rest_created(self, data):
        return rest_framework.response.Response(
            status=201,
            data={
                'detail': data
            })

    def get(self, request):
        serializer = AlertsGETSerializer(data=request.GET)
        if not serializer.is_valid():
            return self.rest_error(status=400, errors=serializer.errors)

        data = serializer.object
        flavorslugs = data['flavors'].split(',')
        max_count = min(data['max'], 10000)

        flavors = []
        for flavorslug in flavorslugs:
            try:
                flavor = AlertFlavor.objects.get(slug=flavorslug)

            except AlertFlavor.DoesNotExist:
                return self.rest_error(
                    status=404,
                    errors={'flavor': [
                        'Flavor "{}" does not exist.'.format(flavorslug)
                    ]}
                )

            self.check_object_permissions(request, flavor)

            if not flavor.enabled:
                return self.rest_error(
                    status=400,
                    errors={'flavor': [
                        'Flavor "{}" is disabled.'.format(flavorslug)
                    ]}
                )

            flavors.append(flavor)

        alerts = Alert.objects.filter(flavor__in=flavors)
        if data.get('start_time_start'):
            alerts = alerts.filter(start_time__gte=data['start_time_start'])
        if data.get('start_time_end'):
            alerts = alerts.filter(start_time__lte=data['start_time_end'])

        if data.get('end_time_start'):
            alerts = alerts.filter(end_time__gte=data['end_time_start'])
        if data.get('end_time_end'):
            alerts = alerts.filter(end_time__lte=data['end_time_end'])

        if data.get('created_start'):
            alerts = alerts.filter(created__gte=data['created_start'])
        if data.get('created_end'):
            alerts = alerts.filter(created__lte=data['created_end'])

        alerts = alerts.order_by('-created')

        alerts_ser = AlertSerializer(alerts[:max_count], many=True)
        return rest_framework.response.Response(
            {
                'total': alerts.count(),
                'count': len(alerts_ser.data),
                'alerts': alerts_ser.data
            }
        )

    def post(self, request):
        data = request.DATA

        try:
            flavorslug = request.DATA['flavor']
        except KeyError:
            return self.rest_error(
                status=404,
                errors='Flavor not specified in payload.'
            )

        try:
            flavor = AlertFlavor.objects.get(slug=flavorslug)
        except AlertFlavor.DoesNotExist:
            return self.rest_error(
                status=404,
                errors='Flavor "{}" does not exist.'.format(flavorslug)
            )

        self.check_object_permissions(request, flavor)

        if not flavor.enabled:
            return self.rest_error(
                status=400,
                errors='Flavor "{}" is disabled.'.format(flavorslug)
            )

        # Get the links out--we'll deal with them next.
        link_data = data.pop('links', [])

        # Validate the alert data
        alert_ser = AlertSerializer(data=data)
        if not alert_ser.is_valid():
            return self.rest_error(
                status=400,
                errors=alert_ser.errors
            )

        # Validate links
        for link_item in link_data:
            if 'name' not in link_item or 'url' not in link_item:
                link_errors = 'Missing names or urls in link data. {}'.format(
                    repr(link_data))

                return self.rest_error(
                    status=400,
                    errors={'links': link_errors}
                )

        # Everything is good, so let's save it all to the db
        alert = alert_ser.object
        alert.save()

        for link_item in link_data:
            link = Link(
                alert=alert, name=link_item['name'], url=link_item['url']
            )
            link.save()

        return self.rest_created({'id': alert.id})
