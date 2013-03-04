from fjord.base.tests import with_save
from fjord.feedback.models import Response


@with_save
def response(**kwargs):
    """Model maker for feedback.models.Response."""
    defaults = {
        'prodchan': 'firefox.desktop.stable'
        }
    defaults.update(kwargs)
    return Response(**defaults)
