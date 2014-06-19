from django.conf import settings


def has_gengo_creds():
    """Returns True if there are GENGO credentials set

    Note: This doesn't verify the credentials--just checks to see if
    they are set.

    """
    return settings.GENGO_PUBLIC_KEY and settings.GENGO_PRIVATE_KEY
