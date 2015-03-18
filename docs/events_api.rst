==========
Events API
==========

.. contents::
   :local:

This covers the Events v1 API. This API is for retrieving events
data.


Getting events: GET /api/v1/events/
===================================

:URL:             ``/api/v1/events/``
:Method:          HTTP GET
:Payload format:  No payload--everything is done in the querystring
:Response:        JSON

Doing a GET without any querystring arguments will return all the event
data.

.. Note::

   This API endpoint is still in flux. The documentation is
   rudimentary at best. Amongst other things, it's difficult to
   discover valid values for things.

   If you're using this API endpoint and have issues, please
   `open a bug
   <https://bugzilla.mozilla.org/enter_bug.cgi?product=Input&rep_platform=all&op_sys=all&component=General>`_.

.. Note::

   The event data is pretty sparse at the moment and only contains
   releases for Firefox and Firefox for Android. We plan to add to
   this data.


Filters
-------

**products**
    Strings. Comma separated list of products. For valid products, see
    `<https://input.mozilla.org/>`_.

    Examples::

        ?products=Firefox
        ?products=Firefox,Firefox for Android

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


Curl example
------------

Minimal example:

::

    curl -v https://input.mozilla.org/api/v1/events/?products=Firefox
