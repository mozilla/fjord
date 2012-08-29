from mobility.decorators import mobile_template
from django.shortcuts import render

from fjord.feedback.models import Simple as SimpleFeedback


@mobile_template('analytics/{mobile/}dashboard.html')
def dashboard(request, template):
    return render(request, template, {
        'opinions': SimpleFeedback.objects.order_by('-created')[:20]
    })
