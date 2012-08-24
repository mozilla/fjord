from mobility.decorators import mobile_template
from django.shortcuts import render


@mobile_template('analytics/{mobile/}dashboard.html')
def dashboard(request, template):
    return render(request, template)
