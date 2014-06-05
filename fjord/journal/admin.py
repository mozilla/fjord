from django.contrib import admin

from .models import Record


class RecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'app',
        'src',
        'type',
        'action',
        'msg',
        'cls_path',
        'obj_id',
        'created',
        'metadata'
    )
    list_filter = ('app', 'src', 'type', 'action', 'cls_path')


admin.site.register(Record, RecordAdmin)
