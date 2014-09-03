from django.contrib import admin

from fjord.flags.models import Flag


class FlagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name'
    )


admin.site.register(Flag, FlagAdmin)
