.. _api-chapter:

=====
 API
=====

.. contents::
   :local:

Fjord has an API.


Testing clients using the API
=============================

.. Warning::

   **DO NOT TEST YOUR CLIENT AGAINST OUR PRODUCTION SERVER. IT WILL
   MAKE CHENG, MATT, TYLER AND I CROSS.**


Seriously. Please don't test your client against our production
server.

Test your client against our stage server which runs the same code
that our production server does. The url for the our stage server is::

    https://input.allizom.org/
                  ^^^^^^^


Please make sure to use the right domain!


Posting product feedback: /api/v1/feedback/
===========================================

:URL:            ``/api/v1/feedback/``
:Method:         HTTP POST
:Payload format: JSON---make sure to have ``Content-type: application/json``
                 header


Required fields
---------------

**happy**
    Boolean. All feedback is either happy or sad. This denotes
    whether this feedback is happy (True) or sad (False).

    Valid values: ``true``, ``false``

**description**
    String. This is the feedback text.

    Example: ``"OMG! I love Firefox!"``

**product**
    String. The name of the product the user is giving feedback on.

    Examples: ``"Firefox for Android"``, ``"Firefox OS"``

    .. Note::

       This must be a valid product in the system. Before you start
       posting to Input, please talk to the User Advocacy folks or an
       Input admin to have your product added.


Optional fields
---------------

**channel**
    String. The channel of the product the user is giving feedback on.

    Examples: ``"stable"``, ``"beta"``

**version**
    String. The version of the product the user is giving feedback
    on as a string.

    Examples: ``"22b2"``, ``"1.1"``

**platform**
    String. The name of the operating system/platform the product
    is running on.

    Examples: ``"OS X"``, ``"Windows 8"``, ``"Firefox OS"``,
    ``"Android"``, ``"Linux"``

**locale**
    String. The locale the user is using.

    Examples: ``"en-US"``, ``"fr"``, ``"de"``

**country**
    String. The country of origin for the device.

    Examples: ``"Peru"``, ``"Mexico"``

    .. Note::

       This is probably only relevant to Firefox OS phones.

**manufacturer**
    String. The manufacturer of the device the product is running
    on.

    Examples: ``"Geeksphone"``, ``"Samsung"``

**device**
    String. The model name of the device the product is running
    on.

    Examples: ``"Peak"``, ``"Galaxy Tab 10.1"``

**url**
    String. If the feedback relates to a specific webpage, then
    the url is the url of the webpage it refers to.

    Examples: ``"https://facebook.com/"``, ``"https://google.com/"``

**email**
    String. The email address of the user. This allows us to
    contact the user at some later point to respond to the user's
    feedback or ask for more information.

    Example: ``"joe@example.com"``

**user_agent**
    String. The user agent of the client if applicable. For example
    if the user is using a Firefox OS device, this would be
    the user agent of the browser used to send feedback.

    Example: ``'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0'``

**source**
    String. If this response was initiated by a blog post, wiki page,
    search, newsletter, tweet or something like that, this is the source
    that initiated the response. It has the same semantics as the 
    utm_source querystring parameter:

    https://support.google.com/analytics/answer/1033867

    Example: ``'Hacks blog'``

**campaign**
    String. If this response was initiated by a marketing campaign,
    this is the name of the campaign. It has the same semantics as
    the utm_campaign querystring parameter:

    https://support.google.com/analytics/answer/1033867
      
    Example: ``'show the firefox love post'``


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
