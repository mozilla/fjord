from mobility.decorators import mobile_template
from django.shortcuts import render


@mobile_template('{mobile/}home.html')
def home_view(request, template=None):
    return render(request, template)
