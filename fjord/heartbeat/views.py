import rest_framework.views
import rest_framework.response
from fjord.base.util import smart_str

from .models import Answer, Poll


class HeartbeatAPI(rest_framework.views.APIView):
    def post(self, request):
        """Handles posting a new heartbeat item"""
        post_data = dict(request.DATA)

        hb = {}

        # Figure out if there's any missing data.
        missing = []
        for key in ('locale', 'platform', 'product', 'version', 'channel',
                    'answer'):
            if key in post_data:
                hb[key] = smart_str(post_data.pop(key))
            else:
                missing.append(key)

        if 'poll' in post_data:
            poll_slug = smart_str(post_data.pop('poll'))
        else:
            missing.append('poll')

        if missing:
            return rest_framework.response.Response(
                status=400,
                data=({'msg': 'missing fields: ' + ', '.join(sorted(missing))})
            )

        # Figure out if the poll exists and is enabled.
        try:
            poll = Poll.objects.get(slug=poll_slug)
        except Poll.DoesNotExist:
            return rest_framework.response.Response(
                status=400,
                data=({'msg': 'poll "%s" does not exist' % poll_slug})
            )

        if not poll.enabled:
            return rest_framework.response.Response(
                status=400,
                data=({'msg': 'poll "%s" is not currently running' %
                       poll_slug})
            )

        hb['poll'] = poll

        # Add the extra POST data fields by tossing them in the
        # "extra" field.
        hb['extra'] = post_data

        hb = Answer(**hb)
        hb.save()

        return rest_framework.response.Response(
            status=201,
            data={'msg': 'success!'})
