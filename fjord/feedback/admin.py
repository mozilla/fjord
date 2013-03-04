from django.contrib import admin
from django.core.exceptions import PermissionDenied

from fjord.feedback.models import Response


class ResponseFeedbackAdmin(admin.ModelAdmin):
    list_display = ('created', 'prodchan', 'happy', 'description',
                    'user_agent', 'locale')
    list_filter = ('prodchan', 'happy', 'locale')
    search_fields = ('description',)

    def has_add_permission(self, request, obj=None):
        # Prevent anyone from adding feedback in the admin.
        return False

    def change_view(self, request, *args, **kwargs):
        # We don't want anyone (including superusers) to change
        # feedback. It's either keep it or delete it.
        #
        # That's sort of difficult with Django without writing a bunch
        # of stuff, so I'm lazily preventing POST here.
        #
        # TODO: Make this better, but push off any changes until other
        # non-superuser people have access to this view and it becomes
        # a relevant issue.
        if request.method == 'POST':
            raise PermissionDenied()

        return super(ResponseFeedbackAdmin, self).change_view(
            request, *args, **kwargs)


admin.site.register(Response, ResponseFeedbackAdmin)
