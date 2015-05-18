============
 Alerts API
============

.. contents::
   :local:

This document covers Alerts v1 API.

The Alerts v1 API is for posting and retrieving alert events. This
data allows us to more easily keep track of trend changes as well as
other events that can be related to user feedback.

If you're interested in posting or retrieving Alerts data, speak to
the User Advocacy group.


Authentication token
====================

Posting to the API requires a valid enabled Token.

To get a token, `write up a bug
<https://bugzilla.mozilla.org/enter_bug.cgi?product=Input&rep_platform=all&op_sys=all>`_
asking for a token. Make sure to state exactly what you'll be using
the token for.

To use a token, include the following HTTP header in your HTTP POST::

    Fjord-Authorization: Token <TOKEN>

where ``<TOKEN>`` is replaced by the token you received.

.. Note::

   Guard this token! If you reveal this token to the public, let us know
   as soon as possible. We will disable the current one and issue a new
   one.


Alert flavors
=============

The alert flavor is the type of alert this is. It allows us to create
a loose grouping of like alerts.

For example, the "mfbt" alert flavor covers all alerts about mfbt.

To get an alert flavor, `write up a bug
<https://bugzilla.mozilla.org/enter_bug.cgi?product=Input&rep_platform=all&op_sys=all>`_
asking for a flavor to be created. Please state exactly what you'll be
using the flavor for. You should probably have a token first since
without the token you can't emit any alerts.

.. Note::

   A single token can GET/POST for multiple flavors, so you can write
   a single emitter that has a single token and have it generate
   alerts of multiple flavors.


POSTing alerts
==============

:URL:            ``/api/v1/alerts/alert/``
:Method:         HTTP POST
:Payload format: JSON---make sure to have ``Content-type: application/json``
                 header
:Response:       JSON


Example
-------

Using curl on the command line::

    curl -v -XPOST 'https://input.mozilla.org/api/v1/alerts/alert/` \
         -H 'Accept: application/json; indent=4' \
         -H 'Content-Type: application/json' \
         -H 'Fjord-Authorization: Token cd64de0e6c4c491f90fe1d362104c1e5' \
         -d '
    {
        "severity": 5,
        "summary": "mfbt now!",
        "description": "it is 4:00pm on a friday and it is mfbt.",
        "flavor": "mfbt",
        "emitter_name": "mfbt-watcher",
        "emitter_version": 1
    }'


Using Python requests:

.. code-block:: python

   import json

   import requests

   headers = {
       'content-type': 'application/json',
       'accept': 'application/json; indent=4',
       'fjord-authorization': 'Token cd64de0e6c4c491f90fe1d362104c1e5',
   }
   payload = {
       'severity': 5,
       'summary': 'mfbt now!',
       'description': 'it is 4:00pm on a friday and it is mfbt.',
       'flavor': 'mfbt',
       'emitter_name': 'mfbt-watcher',
       'emitter_version': 1,
       'start_time': '2015-02-28T07:22:48Z',
       'links': [
           {'name': 'example', 'url': 'http://example.com'}
       ]
   }
   resp = requests.post(
       'https://input.mozilla.org/api/v1/alerts/alert/',
       data=json.dumps(payload),
       headers=headers
   )

   print resp.status_code
   # 201
   print resp.json()
   # something like {u'detail': {u'id': 4}}


Required fields
---------------

These fields are required and have no defaults. If you do not provide
them, then you'll get back an HTTP 400 with a message stating you
missed a required field.

+-------------------+--------+--------------------------------------------------------+
|field              |type    |notes                                                   |
+===================+========+========================================================+
|severity           |integer |This is the severity of the alert. 0 = don't care. 10 = |
|                   |        |call the president.                                     |
+-------------------+--------+--------------------------------------------------------+
|summary            |string  |Brief summary of what the alert is about.               |
+-------------------+--------+--------------------------------------------------------+
|description        |string  |Involved description of all the details that help you   |
|                   |        |understand what this alert is about.                    |
|                   |        |                                                        |
|                   |        |You can make this a JSON encoded field if you have lots |
|                   |        |of key/value pairs you want to include.                 |
+-------------------+--------+--------------------------------------------------------+
|flavor             |string  |The slug of the flavor this alert is for.               |
+-------------------+--------+--------------------------------------------------------+
|emitter_name       |string  |Max length: 100.                                        |
|                   |        |                                                        |
|                   |        |The name of the emitter that created this alert. It     |
|                   |        |could be a script name. It could be a sekret code-name  |
|                   |        |for the emitter. It could be skynet. So long as we can  |
|                   |        |distinguish it from other emitters, it's all good.      |
+-------------------+--------+--------------------------------------------------------+
|emitter_version    |integer |Start with 0.                                           |
|                   |        |                                                        |
|                   |        |Any time you change the shape of the data you're        |
|                   |        |emitting or the kind of data you're emitting in         |
|                   |        |the alert, you should increase the version number.      |
|                   |        |                                                        |
|                   |        |This helps you distinguish between the different        |
|                   |        |versions of alerts that you've pushed so far so that    |
|                   |        |you can parse them differently when you're setting up   |
|                   |        |dashboards or reports about your alerts.                |
+-------------------+--------+--------------------------------------------------------+

Optional fields
---------------

These fields are optional.

+-------------------+---------+--------------------------------------------------------+
|field              |type     |notes                                                   |
+===================+=========+========================================================+
|links              |array of |This is a list of links that are associated with the    |
|                   |objects  |alert.                                                  |
|                   |         |                                                        |
|                   |         |The value is an array of ``{'name': NAME, 'url': URL}`` |
|                   |         |JSON objects.                                           |
+-------------------+---------+--------------------------------------------------------+
|start_time         |iso8601  |The start time of the event this alert is for.          |
|                   |timestamp|                                                        |
|                   |         |Examples:                                               |
|                   |         |                                                        |
|                   |         |* ``'2015-03-02T16:22:10Z'`` - timestamp in UTC         |
|                   |         |* ``'2015-03-02T16:22:10'`` - timezoneless timestamp    |
|                   |         |  which is treated as UTC                               |
|                   |         |* ``'2015-03-02T16:22:10.102Z'`` - timestamp with       |
|                   |         |  milliseconds                                          |
+-------------------+---------+--------------------------------------------------------+
|end_time           |iso8601  |The end time of the event this alert is for.            |
|                   |timestamp|                                                        |
|                   |         |Examples:                                               |
|                   |         |                                                        |
|                   |         |* ``'2015-03-02T16:22:10Z'`` - timestamp in UTC         |
|                   |         |* ``'2015-03-02T16:22:10'`` - timezoneless timestamp    |
|                   |         |  which is treated as UTC                               |
|                   |         |* ``'2015-03-02T16:22:10.102Z'`` - timestamp with       |
|                   |         |  milliseconds                                          |
+-------------------+---------+--------------------------------------------------------+


Responses
---------

All response bodies are in JSON.


HTTP 201: Success
~~~~~~~~~~~~~~~~~

The returned content will have the id of the new alert.


HTTP 400: Bad request
~~~~~~~~~~~~~~~~~~~~~

Answer has errors. Details will be in the response body.

Possibilities include:

* missing name/url in links
* flavor is disabled
* flavor is missing


HTTP 401: Unauthorized
~~~~~~~~~~~~~~~~~~~~~~

The request is invalid or malformed in some way.

* the Fjord-Authorization header was missing
* the Fjord-Authorization header is malformed or missing something


HTTP 403: Forbidden
~~~~~~~~~~~~~~~~~~~

Your token doesn't have permission to GET/POST to the specified alert
flavor.


HTTP 500: Server error
~~~~~~~~~~~~~~~~~~~~~~

Tell Will. He has some 'splaining to do!


GETting alerts
==============

:URL:            ``/api/v1/alerts/alert/``
:Method:         HTTP GET
:Response:       JSON


Arguments are specified in the querystring.

+-------------------+--------+--------------------------------------------------------+
|field              |type    |notes                                                   |
+===================+========+========================================================+
|flavors            |string  |Required. Comma separated list of flavor slugs.         |
|                   |        |                                                        |
|                   |        |Examples::                                              |
|                   |        |                                                        |
|                   |        |    flavors=mfbt                                        |
|                   |        |    flavors=mfbt,cantina                                |
+-------------------+--------+--------------------------------------------------------+
|max                |integer |Default: 100. The maximum number of alerts you want to  |
|                   |        |get back. Maximum is 10000.                             |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    max=1000                                            |
+-------------------+--------+--------------------------------------------------------+
|start_time_start   |datetime|Default: none                                           |
|                   |        |                                                        |
|                   |        |Filter alerts by ``start_time`` >= the                  |
|                   |        |``start_time_start`` value.                             |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    start_time_start=2015-05-13T01:22Z                  |
+-------------------+--------+--------------------------------------------------------+
|start_time_end     |datetime|Default: none                                           |
|                   |        |                                                        |
|                   |        |Filter alerts by ``start_time`` <= the                  |
|                   |        |``start_time_end`` value.                               |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    start_time_end=2015-05-13T01:22Z                    |
+-------------------+--------+--------------------------------------------------------+
|end_time_start     |datetime|Default: none                                           |
|                   |        |                                                        |
|                   |        |Filter alerts by ``end_time`` >= the ``end_time_start`` |
|                   |        |value.                                                  |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    end_time_start=2015-05-13T01:22Z                    |
+-------------------+--------+--------------------------------------------------------+
|end_time_end       |datetime|Default: none                                           |
|                   |        |                                                        |
|                   |        |Filter alerts by ``end_time`` <= the ``end_time_end``   |
|                   |        |value.                                                  |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    end_time_end=2015-05-13T01:22Z                      |
+-------------------+--------+--------------------------------------------------------+
|created_start      |datetime|Default: none                                           |
|                   |        |                                                        |
|                   |        |Filter alerts by ``created`` >= the ``created_start``   |
|                   |        |value.                                                  |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    created_start=2015-05-13T01:22Z                     |
+-------------------+--------+--------------------------------------------------------+
|created_end        |datetime|Default: none                                           |
|                   |        |                                                        |
|                   |        |Filter alerts by ``created`` <= the ``created_end``     |
|                   |        |value.                                                  |
|                   |        |                                                        |
|                   |        |Example::                                               |
|                   |        |                                                        |
|                   |        |    created_end=2015-05-13T01:22Z                       |
+-------------------+--------+--------------------------------------------------------+

Examples
--------

Using curl on the command line::

    curl -v -XGET 'https://input.mozilla.org/api/v1/alerts/alert/?flavors=mfbt' \
         -H 'Accept: application/json; indent=4' \
         -H 'Content-Type: application/json' \
         -H 'Fjord-Authorization: Token cd64de0e6c4c491f90fe1d362104c1e5'

    curl -v -XGET 'https://input.mozilla.org/api/v1/alerts/alert/?flavors=mfbt,cantina' \
         -H 'Accept: application/json; indent=4' \
         -H 'Content-Type: application/json' \
         -H 'Fjord-Authorization: Token cd64de0e6c4c491f90fe1d362104c1e5'


Using Python requests:

.. code-block:: python

   import urllib

   import requests

   headers = {
       'content-type': 'application/json',
       'accept': 'application/json; indent=4',
       'fjord-authorization': 'Token cd64de0e6c4c491f90fe1d362104c1e5',
   }
   qs_params = {
       'flavors': 'mfbt'
   }
   resp = requests.get(
       'https://input.mozilla.org/api/v1/alerts/alert/?' + urllib.urlencode(qs_params),
       headers=headers
   )

   print resp.status_code
   # 200
   print resp.json()
   # alerts data


Using Python requests to get all the alerts created in the last week:

.. code-block:: python

   from datetime import datetime, timedelta

   import requests

   seven_days_ago = datetime.now() - timedelta(days=7)

   headers = {
       'content-type': 'application/json',
       'accept': 'application/json; indent=4',
       'fjord-authorization': 'Token cd64de0e6c4c491f90fe1d362104c1e5',
   }
   qs_params = {
       'flavors': 'mfbt',
       'created_start': seven_days_ago.isoformat()
   }

   url = 'https://input.mozilla.org/api/v1/alerts/alert/?' + urllib.urlencode(qs_params),

   resp = requests.get(url, headers=headers)

   print resp.status_code
   # 200
   print resp.json()
   # alerts data...


Using Python requests to get all the alerts that were "live" between
2015-05-01 and 2015-05-08:

.. code-block:: python

   from datetime import datetime, timedelta

   import requests

   seven_days_ago = datetime.now() - timedelta(days=7)

   headers = {
       'content-type': 'application/json',
       'accept': 'application/json; indent=4',
       'fjord-authorization': 'Token cd64de0e6c4c491f90fe1d362104c1e5',
   }
   qs_params = {
       'flavors': 'mfbt',
       # end_time >= 2015-05-01
       'end_time_start': datetime(2015, 05, 01, 0, 0).isoformat(),
       # start_time <= 2015-05-08
       'start_time_end': datetime(2015, 05, 08, 0, 0).isoformat(),
   }

   url = 'https://input.mozilla.org/api/v1/alerts/alert/?' + urllib.urlencode(qs_params),

   resp = requests.get(url, headers=headers)

   print resp.status_code
   # 200
   print resp.json()
   # alerts data...


Responses
---------

All response bodies are in JSON.

HTTP 200: Success
~~~~~~~~~~~~~~~~~

The returned content is what you asked for.


HTTP 400: Bad request
~~~~~~~~~~~~~~~~~~~~~

The request has errors. Details will be in the response body.

Possibilities include:

* An argument has a bad value. E.g. you passed in a string instead of
  an integer.
* You passed in an argument that doesn't exist. E.g. you passed in
  "mx" instead of "max".
