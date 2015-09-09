from django import forms

from fjord.base.forms import StringListField
from fjord.suggest.providers.trigger.models import TriggerRule


class TriggerRuleForm(forms.ModelForm):
    class Meta:
        model = TriggerRule
        fields = [
            'title',
            'description',
            'slug',
            'url',
            'is_enabled',
            'sortorder',
            'locales',
            'products',
            'versions',
            'url_exists',
            'keywords',
        ]
        help_texts = {
            'url': (
                u'Required. URL for the suggestion. Allows for interpolation '
                u'for {PRODUCT}, {VERSION}, {PLATFORM}, {LOCALE}, and {HAPPY} '
                u'feedback response data.'
            )
        }
        labels = {
            'url_exists': u'Require a url',
            'sortorder': u'Sort order'
        }

    locales = StringListField(
        required=False,
        help_text=u'Locales to match. Each on a separate line.'
    )
    versions = StringListField(
        required=False,
        help_text=(
            u'Versions to match. Each on a separate line. Use "*" at the '
            u'end to do a prefix match. For example "38*" will match all '
            u'versions that start with "38".'
        )
    )
    keywords = StringListField(
        required=False,
        help_text=u'Key words and phrases to match. Each on a separate line.'
    )
