from django import forms

from fjord.heartbeat.models import Survey


class SurveyCreateForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = [
            'enabled',
            'name',
            'description',
        ]
