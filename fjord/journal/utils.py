from .models import Record, RECORD_INFO, RECORD_ERROR


def j_info(app, src, action, msg, instance=None, metadata=None):
    """Generate an INFO record in the journal."""
    return Record.objects.log(
        app=app,
        type_=RECORD_INFO,
        src=src,
        action=action,
        msg=msg,
        instance=instance,
        metadata=metadata)

def j_error(app, src, action, msg, instance=None, metadata=None):
    """Generate an ERROR record in the journal."""
    return Record.objects.log(
        app=app,
        type_=RECORD_ERROR,
        src=src,
        action=action,
        msg=msg,
        instance=instance,
        metadata=metadata)
