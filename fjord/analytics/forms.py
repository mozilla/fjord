from django import forms

from fjord.feedback.models import Product


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
