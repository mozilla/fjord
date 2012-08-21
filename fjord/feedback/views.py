from mobility.decorators import mobile_template
from django.shortcuts import render

from fjord.feedback import forms


def feedback_router(request, *args, **kwargs):
    # Eventually route based on user agent. For now just go ahead.
    return desktop_feedback(request, *args, **kwargs)


@mobile_template('{mobile/}feedback.html')
def desktop_feedback(request, template=None):
    return render(request, template, {
        'forms': {
            'happy': forms.SimpleForm(),
            'sad': forms.SimpleForm()
        }
    })
