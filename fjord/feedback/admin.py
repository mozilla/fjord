from django.contrib import admin
from django.core.exceptions import PermissionDenied

from fjord.feedback.models import Product, Response


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'enabled',
        'on_dashboard',
        'display_name',
        'db_name',
        'translation_system',
        'notes',
        'slug')
    list_filter = ('enabled', 'on_dashboard')


class EmptyFriendlyAVFLF(admin.AllValuesFieldListFilter):
    def choices(self, cl):
        """Displays empty string as <Empty>

        This makes it possible to choose Empty in the filter
        list. Otherwise empty strings display as '' and don't get any
        height and thus aren't selectable.

        """
        for choice in super(EmptyFriendlyAVFLF, self).choices(cl):
            if choice.get('display') == '':
                choice['display'] = '<Empty>'
            yield choice


class ResponseFeedbackAdmin(admin.ModelAdmin):
    list_display = ('created', 'product', 'channel', 'version', 'happy',
                    'description', 'user_agent', 'locale')
    list_filter = ('happy', ('product', EmptyFriendlyAVFLF),
                   ('locale', EmptyFriendlyAVFLF))
    search_fields = ('description',)
    actions = ['nix_product']
    list_per_page = 200

    def nix_product(self, request, queryset):
        ret = queryset.update(product=u'')
        self.message_user(request, '%s responses updated.' % ret)
    nix_product.short_description = u'Remove product for selected responses'

    def queryset(self, request):
        # Note: This ignores the super() queryset and uses the
        # uncached manager.
        return Response.uncached.all()

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


admin.site.register(Product, ProductAdmin)
admin.site.register(Response, ResponseFeedbackAdmin)
