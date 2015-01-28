import rest_framework.views
import rest_framework.response
from statsd import statsd

from .models import Answer, AnswerSerializer
from fjord.base.utils import cors_enabled
from fjord.journal.utils import j_error


class HeartbeatV2API(rest_framework.views.APIView):

    @classmethod
    def as_view(cls, **initkwargs):
        # Enable CORS
        view = super(HeartbeatV2API, cls).as_view(**initkwargs)
        return cors_enabled('*', methods=['POST'])(view)

    def rest_error(self, post_data, errors):
        statsd.incr('heartbeat.error')
        j_error('heartbeat', 'HeartbeatV2API', 'post', 'packet errors',
                metadata={
                    'post_data': post_data,
                    'errors': errors
                })
        return rest_framework.response.Response(
            status=400,
            data={
                'msg': 'bad request; see errors',
                'errors': errors
            }
        )

    def rest_success(self):
        statsd.incr('heartbeat.success')
        return rest_framework.response.Response(
            status=201,
            data={'msg': 'success!'})

    def post(self, request):
        post_data = dict(request.DATA)

        serializer = AnswerSerializer(data=post_data)
        if not serializer.is_valid():
            return self.rest_error(post_data, serializer.errors)

        valid_data = serializer.object

        # Check to see if there's an Answer for this already. If so,
        # fetch it so we can update it. If not, create a new one.
        #
        # FIXME: It's possible we can do this (reuse an object or
        # create a new one) inside the AnswerSerializerDRF, too,
        # but I don't have more time to investigate.
        try:
            ans = Answer.objects.get(
                person_id=valid_data.person_id,
                survey_id=valid_data.survey_id,
                flow_id=valid_data.flow_id
            )
        except Answer.DoesNotExist:
            # If the answer doesn't exist yet, then we take the one
            # from the serializer and save it and we're done.
            serializer.save()
            return self.rest_success()

        # We're updating an existing answer.

        # Check the updated timestamp. If it's the same or older, we throw
        # an error and skip it.
        if post_data['updated_ts'] <= ans.updated_ts:
            # FIXME: statsd, errorlog
            return self.rest_error(
                post_data,
                {'updated_ts': ('updated timestamp is same or older than '
                                'existing data')})

        # Everything is valid, so we update the Answer and save it.

        # Go through all the fields we want to save except
        # survey--that's already all set.
        for field in Answer._meta.fields:
            field_name = field.name
            if field_name in ('id', 'survey_id'):
                continue

            if field_name in post_data:
                setattr(ans, field_name, post_data[field_name])

        ans.save()
        return self.rest_success()
