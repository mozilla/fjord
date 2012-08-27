from django import forms


class URLInput(forms.TextInput):
    """Text field with HTML5 URL Input type."""
    input_type = 'url'


class SimpleForm(forms.Form):
    """Feedback form fields shared between feedback types."""

    # NB: The class 'url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    url = forms.URLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://', 'class': 'url'}))

    description = forms.CharField(widget=forms.Textarea(), required=True)
    # required=False means this allowed to be False, not that it can be blank.
    happy = forms.BooleanField(required=False, widget=forms.HiddenInput())
