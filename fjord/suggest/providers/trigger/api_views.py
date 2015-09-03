from django.utils.decorators import method_decorator

import rest_framework.response
import rest_framework.views
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication

from fjord.base.api_utils import StrictArgumentsMixin
from fjord.base.utils import (
    analyzer_required,
    cors_enabled,
)
from fjord.feedback.models import Response as FeedbackResponse
from fjord.suggest.providers.trigger.models import TriggerRuleMatcher


class TriggerRuleTestSerializer(StrictArgumentsMixin, serializers.Serializer):
    locales = serializers.ListField(
        child=serializers.CharField(trim_whitespace=True, allow_blank=False))
    products = serializers.ListField(
        child=serializers.CharField(trim_whitespace=True, allow_blank=False))
    versions = serializers.ListField(
        child=serializers.CharField(trim_whitespace=True, allow_blank=False))
    keywords = serializers.ListField(
        child=serializers.CharField(trim_whitespace=True, allow_blank=False))
    url_exists = serializers.NullBooleanField()


class CSRFLessSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class TriggerRuleMatchViewAPI(rest_framework.views.APIView):
    authentication_classes = (CSRFLessSessionAuthentication,)

    @classmethod
    def as_view(cls, **initkwargs):
        # Enable CORS
        view = super(TriggerRuleMatchViewAPI, cls).as_view(**initkwargs)
        return cors_enabled('*', methods=['POST'])(view)

    def rest_error(self, errors):
        return rest_framework.response.Response(
            status=400,
            data={
                'msg': 'bad request; see errors',
                'detail': errors
            }
        )

    @method_decorator(analyzer_required)
    def post(self, request):
        NUM_MATCHES = 20

        serializer = TriggerRuleTestSerializer(data=request.data)

        if not serializer.is_valid():
            raise exceptions.ValidationError({'detail': serializer.errors})

        data = serializer.validated_data

        trm = TriggerRuleMatcher(
            locales=data['locales'],
            product_names=data['products'],
            versions=data['versions'],
            url_exists=data['url_exists'],
            keywords=data['keywords'],
        )

        # Look for matches in the most recent 1000 items. We do it this
        # way rather than try to do some filtering in the db so that we
        # don't have two different matching methodologies which will lead
        # to subtle differences. In this case it's better to be 100%
        # accurate than more optimally fast.
        objs = FeedbackResponse.objects.order_by('-id')[:1000]
        matched_objs = []
        for obj in objs:
            if trm.match(obj):
                matched_objs.append(obj)
                if len(matched_objs) >= NUM_MATCHES:
                    break

        objs = [
            {
                'id': obj.id,
                'happy': obj.happy,
                'description': obj.description,
                'locale': obj.locale,
                'platform': obj.platform,
                'product': obj.product,
                'version': obj.version,
                'url': obj.url,
                'created': obj.created,
            }
            for obj in matched_objs
        ]

        return rest_framework.response.Response(
            status=200,
            data={
                'count': len(objs),
                'results': objs
            }
        )
