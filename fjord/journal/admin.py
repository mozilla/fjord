from django.contrib import admin

from fjord.journal.models import Record


class RecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'app',
        'src',
        'type',
        'action',
        'msg',
        'content_type',
        'object_id',
        'content_object',
        'created',
        'metadata'
    )
    list_filter = ('app', 'src', 'type', 'action', 'content_type')


admin.site.register(Record, RecordAdmin)
