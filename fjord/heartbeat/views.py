import rest_framework.views
import rest_framework.response

from fjord.base.utils import RatelimitThrottle


class HeartbeatV2API(rest_framework.views.APIView):
    # FIXME: Implement

    def post(self, request):
        return rest_framework.response.Response(
            status=201,
            data={'msg': 'success!'})

    def get_throttles(self):
        """Return throttle class instances"""
        return [
            RatelimitThrottle(
                rulename='api_hb_post_50ph',
                rate='50/h'),
        ]
