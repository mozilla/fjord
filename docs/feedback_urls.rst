.. _feedback_urls:

===============
 Feedback URLs
===============

Generic URL
===========

The basic URL is this::

    https://input.mozilla.org/feedback

Users sent to that URL will be redirected to a locale-based URL based
on the HTTP headers their browser sends.

The locale-base URL version of this URL will show the product picker
letting the user pick the product they want to leave feedback for.

However, you probably don't want to use the Generic URL---you know
what product you're asking users to leave feedback for, so you should
provide the product in the url.


Product URLs
============

Product urls have this form::

    https://input.mozilla.org/feedback/%PRODUCT%/%VERSION%/
    https://input.mozilla.org/%LOCALE%/feedback/%PRODUCT%/%VERSION%/

This allows you to specify the locale, product and version.

``locale``
    You can provide this if you know what locale you want the user to
    leave feedback for.

    Alternatively, you can leave this out and the user will see the
    feedback form in a locale based on the HTTP headers of the request.

``product``
    The product is the slug of the product that is set up on Input. If you
    haven't had your product set up on Input, you must do that
    first. Please `file a bug <https://bugzilla.mozilla.org/enter_bug.cgi?comment=Please+set+up+a+new+product+for+me.%0A%0aDETAILS+HERE&summary=new+product&product=Input&component=General>`_.

``version``
    Any string that represents the product version. e.g. ``3.0``, ``33.1.1``,
    etc.


Examples:

Firefox desktop::

    https://input.mozilla.org/feedback/firefox
    https://input.mozilla.org/en-US/feedback/firefox
    https://input.mozilla.org/pt-BR/feedback/firefox/29.0

Firefox for Android::

    https://input.mozilla.org/feedback/android
    https://input.mozilla.org/en-US/feedback/android
    https://input.mozilla.org/de/feedback/android/29.0

Firefox OS::

    https://input.mozilla.org/feedback/fxos
    https://input.mozilla.org/en-US/feedback/fxos
    https://input.mozilla.org/es/feedback/fxos/1.3.0.0


Source/Campaign
===============

If you're writing an email, blog post, tweet, whatever and link to
Input feedback form, you should specify the ``utm_source`` and
``utm_campaign`` querystring parameters. For example::

    https://input.mozilla.org/feedback/firefox?utm_source=wiki&utm_campaign=wiki_example

For example, you have a link in the Help menu of the product, you would
probably use::

    utm_source=helpmenu

For example, if you wrote up a blog post on a blog called "Sam's Dev Blog"
asking people for their feedback because you've made some change, you would
probably use::

    utm_source=samsdevblog&utm_campaign=20141124_feedback_request


.. Note::
   
   When you specify ``utm_campaign`` the resulting feedback is considered
   non-organic feedback because you requested the feedback. This is distinguished
   from organic feedback where the user leaves feedback as they so desire.
