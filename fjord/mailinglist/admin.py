from django.contrib import admin

from fjord.mailinglist.models import MailingList


class MailingListAdmin(admin.ModelAdmin):
    list_display = ('name', 'members')


admin.site.register(MailingList, MailingListAdmin)
