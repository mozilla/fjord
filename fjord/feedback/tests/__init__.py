from fjord.base.tests import with_save
from fjord.feedback.models import Simple


@with_save
def simple(**kwargs):
    """Model maker for feedback.models.Simple."""
    defaults = {
        'prodchan': 'firefox.desktop.stable'
        }
    defaults.update(kwargs)
    return Simple(**defaults)
