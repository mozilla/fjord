from django.contrib import admin

from fjord.alerts.models import Alert, AlertFlavor, Link


class AlertFlavorAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'enabled', 'description', 'more_info',
        'default_severity'
    )
    list_filter = ('enabled',)


admin.site.register(AlertFlavor, AlertFlavorAdmin)


class LinkInline(admin.TabularInline):
    model = Link


class AlertAdmin(admin.ModelAdmin):
    list_display = (
        'severity', 'summary', 'flavor', 'emitter_name', 'emitter_version',
        'created'
    )
    list_filter = ('flavor', 'severity', 'emitter_name')
    inlines = [LinkInline]


admin.site.register(Alert, AlertAdmin)
