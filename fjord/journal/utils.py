from .models import Record, RECORD_INFO, RECORD_ERROR
from fjord.base.util import class_to_path


def j_info(app, src, action, msg, instance=None, metadata=None):
    """Generate an INFO record in the journal."""
    if instance is not None:
        cls_path = class_to_path(instance.__class__)
        obj_id = instance.id
    else:
        cls_path = u''
        obj_id = None

    return Record.objects.log(
        app=app,
        type_=RECORD_INFO,
        src=src,
        action=action,
        msg=msg,
        cls_path=cls_path,
        obj_id=obj_id,
        metadata=metadata)

def j_error(app, src, action, msg, instance=None, metadata=None):
    """Generate an ERROR record in the journal."""
    if instance is not None:
        cls_path = class_to_path(instance.__class__)
        obj_id = instance.id
    else:
        cls_path = u''
        obj_id = None

    return Record.objects.log(
        app=app,
        type_=RECORD_ERROR,
        src=src,
        action=action,
        msg=msg,
        cls_path=cls_path,
        obj_id=obj_id,
        metadata=metadata)
