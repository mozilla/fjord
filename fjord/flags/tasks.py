from django.db.models.signals import post_save

from celery import task

from fjord.feedback.models import Response
from fjord.flags.models import Flag


def classify(response, flag):
    # FIXME: Do the spicedham thing here.
    return False


@task()
def classify_task(response_id):
    """Classifies a response as spam or abuse

    Note: We only classify en-US responses. Do not use this with
    non-en-US responses!

    """
    try:
        resp = Response.objects.get(pk=response_id)
    except Response.DoesNotExist:
        return

    # Run the response through the classifier for "spam" and add flag
    # if necessary.
    if classify(resp, 'spam'):
        flagob = Flag.objects.get(name='spam')
        resp.flag_set.add(flagob)

    # Run the response through the classifier for "abuse" and add flag
    # if necessary.
    if classify(resp, 'abuse'):
        flagob = Flag.objects.get(name='abuse')
        resp.flag_set.add(flagob)


def classify_handler(sender, instance=None, created=False, **kwargs):
    """post_save handler to handle classifying"""
    if not created or instance is None:
        return

    if instance.locale != 'en-US':
        return

    classify_task.delay(instance.id)


# Connect this with the Response post_save. This is just for prototype
# purposes so we can see how well spicedham classifies responses. When
# we integrate spicedham, we'll redo the post_save chain for Responses.
post_save.connect(classify_handler, Response, dispatch_uid='.'.join(
    [Response.__module__, Response.__name__, 'classify']))
