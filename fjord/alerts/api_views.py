from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import serializers
import rest_framework.response
import rest_framework.views

from fjord.alerts.models import Alert, AlertFlavor, AlertSerializer, Link
from fjord.api_auth.api_utils import TokenAuthentication
from fjord.base.api_utils import NotFound, StrictArgumentsMixin


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


class AlertsGETSerializer(StrictArgumentsMixin, serializers.Serializer):
    """Serializer that validates GET API arguments"""
    flavors = serializers.CharField(required=True)
    max = serializers.IntegerField(default=100, min_value=1)
    start_time_start = serializers.DateTimeField(required=False)
    start_time_end = serializers.DateTimeField(required=False)

    end_time_start = serializers.DateTimeField(required=False)
    end_time_end = serializers.DateTimeField(required=False)

    created_start = serializers.DateTimeField(required=False)
    created_end = serializers.DateTimeField(required=False)

    def validate(self, data):
        data = super(AlertsGETSerializer, self).validate(data)
        errors = []

        if is_after(data.get('start_time_start'), data.get('start_time_end')):
            errors.append('start_time_start must occur before start_time_end.')

        if is_after(data.get('end_time_start'), data.get('end_time_end')):
            errors.append('end_time_start must occur before end_time_end.')

        if is_after(data.get('created_start'), data.get('created_end')):
            errors.append('created_start must occur before created_end.')

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def validate_flavors(self, value):
        flavorslugs = value.split(',')
        flavors = []
        errors = []

        for flavorslug in flavorslugs:
            try:
                flavor = AlertFlavor.objects.get(slug=flavorslug)

            except AlertFlavor.DoesNotExist:
                errors.append(
                    'Flavor "{0}" does not exist.'.format(flavorslug)
                )
                continue

            if not flavor.enabled:
                errors.append(
                    'Flavor "{0}" is disabled.'.format(flavorslug)
                )
                continue

            flavors.append(flavor)

        if errors:
            raise serializers.ValidationError(errors)

        # Return a list of the validated AlertFlavor objects. We're
        # (ab)using validate_flavors here since we should only be
        # doing validation, but since doing the validation also
        # transforms the slugs into AlertFlavor objects, we'll do them
        # both here.
        return flavors


class AlertsAPI(rest_framework.views.APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (FlavorPermission,)

    def get(self, request):
        serializer = AlertsGETSerializer(data=request.GET)

        if not serializer.is_valid():
            raise exceptions.ValidationError({'detail': serializer.errors})

        data = serializer.validated_data
        max_count = min(data['max'], 10000)
        flavors = data['flavors']

        # Make sure the token has permission to view each flavor.
        for flavor in flavors:
            self.check_object_permissions(request, flavor)

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
        data = request.data

        try:
            flavorslug = data['flavor']
        except KeyError:
            raise exceptions.ValidationError({
                'flavor': [
                    'Flavor not specified in payload'
                ]
            })

        try:
            flavor = AlertFlavor.objects.get(slug=flavorslug)
        except AlertFlavor.DoesNotExist:
            raise NotFound({
                'flavor': [
                    'Flavor "{0}" does not exist.'.format(flavorslug)
                ]
            })

        self.check_object_permissions(request, flavor)

        if not flavor.enabled:
            raise exceptions.ValidationError({
                'flavor': [
                    'Flavor "{0}" is disabled.'.format(flavorslug)
                ]
            })

        # Get the links out--we'll deal with them next.
        link_data = data.pop('links', [])

        # Validate the alert data
        alert_ser = AlertSerializer(data=data)
        if not alert_ser.is_valid():
            raise exceptions.ValidationError({'detail': alert_ser.errors})

        # Validate links
        link_errors = []
        for link_item in link_data:
            if 'name' not in link_item or 'url' not in link_item:
                link_errors.append(
                    'Missing names or urls in link data. {}'.format(
                        repr(link_item)))

        if link_errors:
            raise exceptions.ValidationError(
                {'detail': {'links': link_errors}})

        # Everything is good, so let's save it all to the db.
        alert = alert_ser.save()

        for link_item in link_data:
            link = Link(
                alert=alert, name=link_item['name'], url=link_item['url']
            )
            link.save()

        return rest_framework.response.Response(
            status=201,
            data={
                'detail': {'id': alert.id}
            })
