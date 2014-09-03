.. _api-chapter:

=====
 API
=====

.. contents::
   :local:

Fjord has several POST APIs and one GET API for data.


Getting product feedback: GET /api/v1/feedback/
===============================================

:URL:            ``/api/v1/feedback/``
:Method:         HTTP GET
:Payload format: There is no payload--everything is done in the querystring


Doing a GET without any querystring arguments will return the most
recent 1,000 publicly visible responses for all products.

.. Warning::

   This API endpoint is throttled. If you hit it too often, you'll get
   throttled. You just need to wait a bit for the throttle to expire.


.. Note::

   This API endpoint is still in flux. The documentation is
   rudimentary at best. Amongst other things, it's difficult to
   discover valid values for things.

   If you're using this API endpoint and have issues, please
   `open a bug
   <https://bugzilla.mozilla.org/enter_bug.cgi?product=Input&rep_platform=all&op_sys=all&component=General>`_.


Filters
-------

**q**
    String. Text query.

    Example::

        ?q=crash

**happy**
    Boolean. ``0`` or ``1``. Restricts results to either happy feedback or
    sad feedback.

    Example::

        ?happy=0

**platforms**
    Strings. Comma separated list of platforms. For valid platforms, see
    `<https://input.mozilla.org/>`_.

    Examples::

        ?platforms=linux
        ?platforms=linux,os x

**locales**
    Strings. Comma separated list of locales. For valid locales, see
    `<https://input.mozilla.org/>`_.

    Examples::

        ?locales=en-US
        ?locales=en-US,es,es-BR

**products**
    Strings. Comma separated list of products. For valid products, see
    `<https://input.mozilla.org/>`_.

    Examples::

        ?products=Firefox
        ?products=Firefox OS,Firefox

**versions**
    Strings. Comma separated list of versions for a specific product. For
    valid versions, see `<https://input.mozilla.org/>`_.

    You must specify a product in order to specify versions.

    Examples::

        ?products=Firefox&versions=31.0
        ?products=Firefox&versions=31.0,32.0

**date_start**
    Date in YYYY-MM-DD format. Specifies the start for the date range you're
    querying for.

    Example::

        ?date_start=2014-08-12

**date_end**
    Date in YYYY-MM-DD format. Specifies the end for the date range you're
    querying for.

    Defaults to today.

    Example::

        ?date_end=2014-08-12

**date_delta**
    ``1d``, ``7d``, ``14d``. The number of days from ``date_start`` or
    ``date_end``.

    Example::

        # Shows the last 7 days ending today
        ?date_delta=7d

        # Shows 14 days ending 2014-08-12
        ?date_end=2014-08-12&date_delta=14d

        # Shows 14 days starting 2014-08-12
        ?date_start=2014-08-12&date_delta=14d

**max**

    Integer. Defaults to 1,000. Maximum is 10,000. Minimum is 1. The maximum
    number of responses you want to get back.

    Example::

        # Retrieve at most 500 responses
        ?max=500

        # Retrieve at most 10000 responses
        ?max=10000


Examples
--------

Show all the happy responses for Firefox for the last 7 days for the
English locale::

    ?happy=1&products=Firefox&locales=en-US&date_delta=7d

Show sad responses for Windows platforms for the last day::

    ?happy=0&platforms=Windows 7,Windows XP, Windows 8.1,Windows 8,Windows Vista,Windows NT&date_delta=1d



Posting product feedback: POST /api/v1/feedback/
================================================

:URL:            ``/api/v1/feedback/``
:Method:         HTTP POST
:Payload format: JSON---make sure to have ``Content-type: application/json``
                 header


Testing clients using the API
-----------------------------

.. Warning::

   **DO NOT TEST YOUR CLIENT AGAINST OUR PRODUCTION SERVER. IT WILL
   MAKE CHENG, MATT, TYLER AND I CROSS.**


Seriously. Please don't test your client against our production
server.

Test your client against our stage server which runs the same code
that our production server does. The url for the our stage server is::

    https://input.allizom.org/
                  ^^^^^^^


Please make sure to use the correct domain!


Required fields
---------------

**happy**
    Boolean. All feedback is either happy or sad. This denotes
    whether this feedback is happy (True) or sad (False).

    Valid values: ``true``, ``false``

**description**
    String. Max length: None (but 10,000 characters is probably a good cutoff).
    This is the feedback text.

    Example: ``"OMG! I love Firefox!"``

    .. Note::

       The form this field is on should have some informational text
       stating that data in this field will be publicly available and
       that the user should not include personally identifyable
       information.

       Example informational text::

           The content of your feedback will be public, so please be sure
           not to include any personal information.

**product**
    String. Max length: 20. The name of the product the user is giving
    feedback on.

    Examples:``"Firefox for Android"``, ``"Firefox OS"``

    .. Note::

       This must be a valid product in the system. Before you start
       posting to Input, please talk to the User Advocacy folks or an
       Input admin to have your product added.


Optional fields
---------------

**channel**
    String. Max length: 30. The channel of the product the user is
    giving feedback on.

    Examples: ``"stable"``, ``"beta"``

**version**
    String. Max length: 30. The version of the product the user is
    giving feedback on as a string.

    Examples: ``"22b2"``, ``"1.1"``

**platform**
    String. Max length: 30. The name of the operating system/platform
    the product is running on.

    Examples: ``"OS X"``, ``"Windows 8"``, ``"Firefox OS"``,
    ``"Android"``, ``"Linux"``

**locale**
    String. Max length: 8. The locale the user is using.

    Examples: ``"en-US"``, ``"fr"``, ``"de"``

**country**
    String. Max length: 30. The country of origin for the device.

    Examples: ``"Peru"``, ``"Mexico"``

    .. Note::

       This is only relevant to Firefox OS phones.

**manufacturer**
    String. Max length: 255. The manufacturer of the device the
    product is running on.

    Examples: ``"Geeksphone"``, ``"Samsung"``

**device**
    String. Max length: 255. The model name of the device the product
    is running on.

    Examples: ``"Peak"``, ``"Galaxy Tab 10.1"``

**category**
    String. Max length: 50. The category classification for this
    feedback response.

    Examples: ``"ui"``, ``"performance"``, ``"bookmarks"``

**url**
    String. Max length: 200. If the feedback relates to a specific
    webpage, then the url is the url of the webpage it refers to.

    Examples: ``"https://facebook.com/"``, ``"https://google.com/"``

**email**
    String. The email address of the user. This allows us to
    contact the user at some later point to respond to the user's
    feedback or ask for more information.

    Example: ``"joe@example.com"``

    .. Note::

       The form this field is in should state that email addresses
       will not be publicly available.

       Example informational text::

           While your feedback will be publicly visible, email addresses
           are kept private. We understand your privacy is important.

**user_agent**
    String. Max length: 255. The user agent of the client if
    applicable. For example if the user is using a Firefox OS device,
    this would be the user agent of the browser used to send feedback.

    Example: ``'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0'``

**source**
    String. Max length: 100. If this response was initiated by a blog
    post, wiki page, search, newsletter, tweet or something like that,
    this is the source that initiated the response. It has the same
    semantics as the utm_source querystring parameter:

    https://support.google.com/analytics/answer/1033867

    Example: ``'Hacks blog'``

**campaign**
    String. Max length: 100. If this response was initiated by a
    marketing campaign, this is the name of the campaign. It has the
    same semantics as the utm_campaign querystring parameter:

    https://support.google.com/analytics/answer/1033867

    Example: ``'show the firefox love post'``


Extra context
-------------

You can provide additional context in the form of key/value pairs by
adding additional data to the JSON object.

Any fields that aren't part of the required or optional fields list
will get thrown into a JSON object and dumped in the feedback response
context.

For example, if the product were the Firefox devtools and you want
feedback responses to include the theme (dark or light) that the user
was using, you could add this to the JSON object::

    {
        "happy": true,
        "description": "devtools are the best!",
        "product": "Devtools",
        "theme": "dark"
    }


That last key will get added to the feedback response context.

.. Note::

   Obviously, don't use a key that's already the name of a
   field. Also, since this is not future proof, you might want to
   prepend a unique string to any keys you add.


.. Note::

   It's important you don't add ids or data that allows you to
   correlate feedback responses to things in other data sets. That
   violates our privacy policy.


Minimal example with curl
-------------------------

::

    $ curl -v -XPOST 'https://input.allizom.org/api/v1/feedback' \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "happy": true,
        "description": "Posting by api!",
        "product": "Firefox"
    }'


Responses
---------

After posting feedback, you'll get one of several responses:


HTTP 201
    Feedback was posted successfully.

HTTP 400
    Feedback has errors. Details will be in the response body.

    Possibilities include:

    * missing required fields
    * email address is malformed
    * data is in the wrong format

HTTP 429
    There has been too many feedback postings from this IP address and
    the throttle trigger was hit. Try again later.


Posting heartbeat feedback: /api/v1/hb/
=======================================

:URL:            ``/api/v1/hb/``
:Method:         HTTP POST
:Payload format: JSON--make sure to have ``Content-type: application/json``
                 header


Testing clients using the API
-----------------------------

.. Warning::

   **DO NOT TEST YOUR CLIENT AGAINST OUR PRODUCTION SERVER. IT WILL
   MAKE CHENG, MATT, TYLER AND I CROSS.**


Seriously. Please don't test your client against our production
server.

Test your client against our stage server which runs the same code
that our production server does. The url for the our stage server is::

    https://input.allizom.org/
                  ^^^^^^^


Please make sure to use the correct domain!


Required fields
---------------

**locale**
    String. Max length: 8. The locale of the user interface that the
    user is using

    Examples:``"en-US"``, ``"fr"``, ``"de"``

**platform**
    String. Max length: 30. The name of the operating system/platform
    the product is running on.

    Examples: ``"OS X"``, ``"Windows 8"``, ``"Firefox OS"``,
    ``"Android"``, ``"Linux"``

**product**
    String. Max length: 30. The name of the product the user is giving
    feedback on.

    Examples:``"Firefox for Android"``, ``"Firefox OS"``

    .. Note::

       This must be a valid product in the system. Before you start
       posting to Input, please talk to the User Advocacy folks or an
       Input admin to have your product added.

**channel**
    String. Max length: 30. The channel of the product the user is
    giving feedback on.

    Examples:``"stable"``, ``"beta"``

**version**
    String. Max length: 30. The version of the product the user is
    giving feedback on as a string.

    Examples:``"22b2"``, ``"1.1"``


    String. The operating system the user is using

**poll**
    String. Max length: 50. Alpha-numeric characters and ``-`` only. The
    slug of the poll this heartbeat response is for.

    Examples:``"is-firefox-fast"``

    .. Note::

       The poll must be created on the Input system you're testing
       against and enabled. Otherwise you'll get errors.

       Before you start posting to Input, please talk to the User
       Advocacy folks or an Input admin to have your product added.

**answer**
    String. Max length: 10. The answer value.

    Examples: ``"true"``, ``"false"``, ``"4"``


Extra data
    Any additional fields you provide in the POST data will get
    glommed into a JSON object and stuck in the db.


Curl examples
-------------

Minimal example:

::

    curl -v -XPOST $URL \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "locale": "en-US",
        "platform": "Linux",
        "product": "Firefox",
        "version": "30.0",
        "channel": "stable",
        "poll": "ou812",
        "answer": "42"
    }'


Here's an example providing "extra" data:

::

    curl -v -XPOST $URL \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "locale": "en-US",
        "platform": "Linux",
        "product": "Firefox",
        "version": "30.0",
        "channel": "stable",
        "poll": "ou812",
        "answer": "42",
        "favoritepie": "cherry",
        "favoriteUAperson": "tyler"
    }'

The extra fields are plucked out and put in a JSON object and stored
in the db like this::

    {"favoritepie": "cherry", "favoriteUAperson": "tyler"}
