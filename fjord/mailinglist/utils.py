from fjord.mailinglist.models import MailingList


def get_recipients(mailinglist_name):
    """Retrieves the list of recipients for a given mailing list

    :arg mailinglist_name: string name for the mailing list

    :returns: list of email addresses which can be used as the
        argument to django.core.email.send_mail recipient_list
        arg

    """
    try:
        ml = MailingList.objects.get(name=mailinglist_name)
        return ml.recipient_list
    except MailingList.DoesNotExist:
        return []
