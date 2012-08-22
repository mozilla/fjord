from mobility.decorators import mobile_template
from django.http import HttpResponse
from django.shortcuts import render

from fjord.feedback.forms import SimpleForm


def feedback_router(request, *args, **kwargs):
    # Eventually route based on user agent. For now just go ahead.
    return desktop_feedback(request, *args, **kwargs)


@mobile_template('{mobile/}feedback.html')
def desktop_feedback(request, template=None):
    forms = {
        'happy': SimpleForm(initial={'happy': True}),
        'sad': SimpleForm(initial={'happy': False}),
    }

    if request.method == 'POST':
        form = SimpleForm(request.POST)
        if form.is_valid():
            ret = 'Form: <ul>'
            ret += '<li>description: %s</li>' % form.cleaned_data['description']
            ret += '<li>url: %s</li>' % form.cleaned_data['url']
            ret += '<li>happy: %s</li>' % form.cleaned_data['happy']
            ret += '</ul>'
            return HttpResponse(ret)
        else:
            if request.POST.get('happy'):
                forms['happy'] = form
            else:
                forms['sad'] = form

    return render(request, template, {'forms': forms})
