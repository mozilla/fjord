from django.contrib import admin

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


admin.site.register(Product, ProductAdmin)
admin.site.register(Response, ResponseFeedbackAdmin)
