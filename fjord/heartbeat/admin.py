from django.contrib import admin

from .models import Survey


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'created')
    list_filter = ('name', 'enabled', 'created')


admin.site.register(Survey, SurveyAdmin)
