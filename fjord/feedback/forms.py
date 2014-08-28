from django import forms

from fjord.base.forms import EnhancedURLField


class URLInput(forms.TextInput):
    """Text field with HTML5 URL Input type."""
    input_type = 'url'


class ResponseForm(forms.Form):
    """Basic response feedback form."""

    # NB: The class 'url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    url = EnhancedURLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://', 'class': 'url'}))

    description = forms.CharField(widget=forms.Textarea(), required=True)
    # required=False means this allowed to be False, not that it can
    # be blank.
    happy = forms.BooleanField(required=False, widget=forms.HiddenInput())

    email_ok = forms.BooleanField(required=False)
    email = forms.EmailField(required=False)

    # These are hidden fields on the form which we have here so we can
    # abuse the fields for data validation.
    manufacturer = forms.CharField(required=False, widget=forms.HiddenInput(
        attrs={'class': 'manufacturer'}))
    device = forms.CharField(required=False, widget=forms.HiddenInput(
        attrs={'class': 'device'}))
