from django import forms

from fjord.feedback.models import Product
from fjord.heartbeat.models import Survey


class ProductsUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'enabled',
            'display_name',
            'display_description',
            'db_name',
            'slug',
            'on_dashboard',
            'on_picker',
            'browser',
            'browser_data_browser',
            'notes'
        ]


class SurveyCreateForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = [
            'enabled',
            'name',
            'description',
        ]
