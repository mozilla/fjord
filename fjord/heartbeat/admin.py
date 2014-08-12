from django.contrib import admin

from .models import Answer, Poll


class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'locale',
        'platform',
        'product',
        'version',
        'channel',
        'extra',
        'poll',
        'answer',
        'created'
    )
    list_filter = ('poll',)


admin.site.register(Answer, AnswerAdmin)


class PollAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'slug',
        'description',
        'status',
        'enabled',
        'created',
    )
    list_filter = ('enabled',)


admin.site.register(Poll, PollAdmin)
