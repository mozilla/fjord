from django.contrib import admin

from fjord.suggest.providers.trigger.models import TriggerRule


class TriggerRuleAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'is_enabled', 'url', 'locales', 'keywords', 'versions',
        'url_exists'
    )
    list_filter = ('is_enabled',)


admin.site.register(TriggerRule, TriggerRuleAdmin)
