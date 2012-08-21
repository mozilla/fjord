from django import forms

from tower import ugettext_lazy as _lazy


class URLInput(forms.TextInput):
    """Text field with HTML5 URL Input type."""
    input_type = 'url'


class SimpleForm(forms.Form):
    """Feedback form fields shared between feedback types."""

    add_url = forms.BooleanField(initial=True, required=False)
    # NB: The class 'url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    # Do not change unless you know what you are doing.
    # TODO @deprecated id == id_url used to be used by the extension.
    url = forms.URLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://', 'class': 'url'}))

    description = forms.CharField(
        widget=forms.Textarea(),
        label=_lazy('Please describe what you liked.'),
        required=True
        )
    happy = forms.BooleanField(required=True)
