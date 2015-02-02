from django import forms

from fjord.feedback.models import Product


class OccurrencesComparisonForm(forms.Form):
    """Form for denoting parameters for the Occurrences Comparison report"""
    product = forms.CharField()

    first_version = forms.CharField(required=False)
    first_search_term = forms.CharField(required=False)
    first_start_date = forms.DateField(help_text='yyyy-mm-dd', required=False)
    first_end_date = forms.DateField(help_text='yyyy-mm-dd', required=False)

    second_version = forms.CharField(required=False)
    second_search_term = forms.CharField(required=False)
    second_start_date = forms.DateField(required=False, help_text='yyyy-mm-dd')
    second_end_date = forms.DateField(required=False, help_text='yyyy-mm-dd')

    def clean(self):
        cleaned_data = super(OccurrencesComparisonForm, self).clean()

        # User must specify at least one of version, search term or
        # start date for the first set otherwise the form is invalid.
        required_values = [
            cleaned_data.get(key, '') for key in
            ('first_version', 'first_search_term', 'first_start_date')]

        if not any(required_values):
            raise forms.ValidationError(
                'Must specify at least one of version, search term or start '
                'date for first set.')

        return cleaned_data


class ProductsUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'enabled',
            'display_name',
            'db_name',
            'slug',
            'on_dashboard',
            'on_picker',
            'notes'
        ]

class LeftDashboard(forms.Form):
    """filters on the left side of dashboard page"""
    date_start = forms.DateField(required = False,widget = forms.DateInput())
    date_end = forms.DateField(required=False,widget = forms.DateInput())
    happy = forms.BooleanField(required=False)
    platform = forms.BooleanField(required=False)
    locale = forms.BooleanField(required=False)
    product  = forms.BooleanField(required=False)
    version  = forms.BooleanField(required=False)