from django.db import IntegrityError, transaction

import rest_framework.views
import rest_framework.response
from statsd.defaults.django import statsd

from .models import Answer, AnswerSerializer
from fjord.base.utils import cors_enabled
from fjord.journal.utils import j_error


def log_error(post_data, errors):
    j_error('heartbeat', 'HeartbeatV2API', 'post', 'packet errors',
            metadata={
                'post_data': post_data,
                'errors': errors
            })


class HeartbeatV2API(rest_framework.views.APIView):
    @classmethod
    def as_view(cls, **initkwargs):
        # Enable CORS
        view = super(HeartbeatV2API, cls).as_view(**initkwargs)
        return cors_enabled('*', methods=['POST'])(view)

    def rest_error(self, post_data, errors, log_errors=True):
        statsd.incr('heartbeat.error')
        if log_errors:
            log_error(post_data, errors)
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
        post_data = dict(request.data)

        # Stopgap fix for 1195747 where the hb client is sending
        # "unknown" which fails validation because the column has
        # max_length 4.
        if post_data.get('country', '') == 'unknown':
            post_data['country'] = 'UNK'

        serializer = AnswerSerializer(data=post_data)
        if not serializer.is_valid():
            return self.rest_error(post_data, serializer.errors)

        valid_data = serializer.validated_data

        # Try to save it and if it kicks up an integrity error, then
        # we already have this object and we should update it with the
        # existing stuff.
        #
        # Note: This is like get_or_create(), but does it in the
        # reverse order so as to eliminate the race condition by
        # having the db enforce integrity.
        try:
            with transaction.atomic():
                serializer.save()
                return self.rest_success()
        except IntegrityError:
            pass

        # Failing the save() above means there's an existing Answer,
        # so we fetch the existing answer to update.
        ans = Answer.objects.get(
            person_id=valid_data['person_id'],
            survey_id=valid_data['survey_id'],
            flow_id=valid_data['flow_id']
        )

        # Check the updated timestamp. If it's the same or older, we
        # throw an error and skip it.
        if post_data['updated_ts'] <= ans.updated_ts:
            # FIXME: statsd, errorlog
            return self.rest_error(
                post_data,
                {'updated_ts': ('updated timestamp is same or older than '
                                'existing data')},
                log_errors=False
            )

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
