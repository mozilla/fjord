import rest_framework.views
import rest_framework.response

from fjord.base.utils import smart_str
from fjord.events.models import get_product_details_history


class EventAPI(rest_framework.views.APIView):
    def get(self, request):
        events = get_product_details_history()

        products = smart_str(request.GET.get('products'))
        date_start = smart_str(request.GET.get('date_start'))
        date_end = smart_str(request.GET.get('date_end'))

        if products:
            products = [prod.strip() for prod in products.split(',')]
            events = [event for event in events
                      if event['product'] in products]

        if date_start:
            events = [event for event in events
                      if event['date'] >= date_start]

        if date_end:
            events = [event for event in events
                      if event['date'] <= date_end]

        return rest_framework.response.Response({
            'date_start': date_start if date_start else None,
            'date_end': date_end if date_end else None,
            'products': ','.join(products) if products else None,
            'count': len(events),
            'events': list(events)
        })

    def get_throttles(self):
        # FIXME: At some point we should throttle use of this. We
        # should probably do that as soon as it's hitting the db.
        return []
