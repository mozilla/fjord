import rest_framework.views
import rest_framework.response

from .models import get_product_details_history
from fjord.base.util import smart_str


class EventAPI(rest_framework.views.APIView):
    def get(self, request):
        events = get_product_details_history()

        product = smart_str(request.GET.get('product'))
        start_date = smart_str(request.GET.get('start_date'))
        end_date = smart_str(request.GET.get('end_date'))

        if product:
            events = [event for event in events
                      if event['product'] == product]

        if start_date:
            events = [event for event in events
                      if event['date'] >= start_date]

        if end_date:
            events = [event for event in events
                      if event['date'] <= end_date]

        return rest_framework.response.Response({
            'count': len(events),
            'events': list(events)
        })

    def get_throttles(self):
        # FIXME
        return []
