from django.contrib import admin

from fjord.heartbeat.models import Survey


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'created', 'description')
    list_filter = ('name', 'enabled', 'created')


admin.site.register(Survey, SurveyAdmin)
