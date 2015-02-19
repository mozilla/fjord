from django.contrib import admin

from fjord.api_auth.models import Token


class TokenAdmin(admin.ModelAdmin):
    list_display = (
        'token', 'summary', 'enabled', 'disabled_reason', 'contact', 'created'
    )
    list_filter = ('enabled',)
    readonly_fields = ('token',)


admin.site.register(Token, TokenAdmin)
