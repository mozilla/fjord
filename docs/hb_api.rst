.. _api-chapter:

===============
 Heartbeat API
===============

.. contents::
   :local:

This covers the Heartbeat v2 API. The v1 API was phased out.

The Heartbeat v2 API is for sending data from Heartbeat survey addons
to Input. The data contains personally identifyable information so we
treat it as such. It is stored in the database and is not publicly
accessible.

If you're interested in Hearbeat data, speak to the User Advocacy
group.


General
=======

:URL:            ``/api/v2/hb/``
:Method:         HTTP POST
:Payload format: JSON---make sure to have ``Content-type: application/json``
                 header
:Response:       JSON


Fields
======

Required
--------

These fields are required and have no defaults. If you do not provide
them, then you'll get back an HTTP 400 with a message stating you
missed a required field.

+----------------+-------+--------------------------------------------------------+
|field           |type   |notes                                                   |
+================+=======+========================================================+
|person_id       |string |max length: 50; Id representating a person's browser.   |
|                |       |Global across surveys and flows.                        |
+----------------+-------+--------------------------------------------------------+
|survey_id       |string |This is the survey name as it is set up in Input. This  |
|                |       |is the only field that has a foreign key to another     |
|                |       |table in Input and must be set up before running a      |
|                |       |survey.                                                 |
|                |       |                                                        |
+----------------+-------+--------------------------------------------------------+
|flow_id         |string |max length: 50; Id uniquely identifying a flow attempt  |
|                |       |for this survey.                                        |
|                |       |                                                        |
|                |       |                                                        |
|                |       |                                                        |
+----------------+-------+--------------------------------------------------------+
|question_id     |string |max length: 50; Id uniquely identifying a question for  |
|                |       |this survey. This allows us to tweak the question text  |
|                |       |for a survey without launching a new survey.            |
|                |       |                                                        |
|                |       |                                                        |
+----------------+-------+--------------------------------------------------------+
|response_version|integer|This is the version of the packet specification. Any    |
|                |       |time the values of the packet or the calculation of the |
|                |       |values for the packet change, we should increase the    |
|                |       |``response_version``. This allows us to distinguish     |
|                |       |between different packet builds when doing analysis.    |
+----------------+-------+--------------------------------------------------------+
|updated_ts      |integer|Milliseconds since the epoch for when this packet was   |
|                |       |created.                                                |
|                |       |                                                        |
|                |       |Every time you update data for a flow attempt, it should|
|                |       |include a new and more recent ``updated_ts``.           |
+----------------+-------+--------------------------------------------------------+
|question_text   |string |Max length: None; Default: ``""``; The actual question  |
|                |       |asked. This can be localized.                           |
+----------------+-------+--------------------------------------------------------+
|variation_id    |string |Max length: 50; Default: ``""``                         |
+----------------+-------+--------------------------------------------------------+


Optional fields
---------------

+---------------+---------+--------------------------------------------------------+
|field          |type     |notes                                                   |
+===============+=========+========================================================+
|score          |float    |Default: ``null``; The answer the user submitted.       |
+---------------+---------+--------------------------------------------------------+
|max_score      |float    |Default: ``null``; The maximum of the answer range.     |
+---------------+---------+--------------------------------------------------------+
|flow_began_ts  |integer  |Default: ``0``; Milliseconds since the epoch of when the|
|               |         |flow began                                              |
+---------------+---------+--------------------------------------------------------+
|flow_offered_ts|integer  |Default: ``0``                                          |
+---------------+---------+--------------------------------------------------------+
|               |integer  |Default: ``0``; Milliseconds since the epoch of when the|
|flow_voted_ts  |         |user submitted an answer.                               |
+---------------+---------+--------------------------------------------------------+
|flow_engaged_ts|integer  |Default: ``0``                                          |
+---------------+---------+--------------------------------------------------------+
|platform       |string   |Max length: 50; Default: ``""``; Operating system and   |
|               |         |version that the user is using.                         |
+---------------+---------+--------------------------------------------------------+
|channel        |string   |Max length: 50; Default: ``""``; The channel of the     |
|               |         |browser that the user is using.                         |
+---------------+---------+--------------------------------------------------------+
|version        |string   |Max length: 50; Default: ``""``; The version of the     |
|               |         |browser that the user is using.                         |
+---------------+---------+--------------------------------------------------------+
|locale         |string   |Max length: 50; Default: ``""``; The locale that the    |
|               |         |user's browser's interface is in.                       |
+---------------+---------+--------------------------------------------------------+
|build_id       |string   |Max length: 50; Default: ``""``                         |
+---------------+---------+--------------------------------------------------------+
|partner_id     |string   |Max length: 50; Default: ``""``                         |
+---------------+---------+--------------------------------------------------------+
|profile_age    |integer  |Default: ``null``; Age in days of the user's browser    |
|               |         |profile.                                                |
+---------------+---------+--------------------------------------------------------+
|profile_usage  |JSON     |Default: ``{}``; JavaScript object of key/value pairs   |
|               |         |with information about profile usage.                   |
+---------------+---------+--------------------------------------------------------+
|addons         |JSON     |Default: ``{}``; JavaScript object of key/value pairs   |
|               |         |with information about the user's addons.               |
+---------------+---------+--------------------------------------------------------+
|extra          |JSON     |Default: ``{}``; Any extra context you want to provide. |
+---------------+---------+--------------------------------------------------------+
|is_test        |boolean  |Default: ``false``; Whether (true) or not (false) this  |
|               |         |is a test packet.                                       |
+---------------+---------+--------------------------------------------------------+


Extra content
-------------

Provide extra content in the ``extra`` field--there is no slop for this API.


Responses
=========

All response bodies are in JSON.

HTTP 201: Success
-----------------

The answer was posted successfully.

Example curl::

    curl -v -XPOST 'https://input.mozilla.org/api/v2/hb/' \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "person_id": "c1dd81f2-6ece-11e4-8a01-843a4bc832e4",
        "survey_id": "lunch",
        "flow_id": "20141117_attempt1",
        "response_version": 1,
        "question_id": "howwaslunch",
        "question_text": "how was lunch?",
        "variation_id": "1",
        "updated_ts": 1416011156000,
        "is_test": true
    }'

yields this response::

    HTTP/1.0 201 CREATED
    <uninteresting headers omitted>
    Content-Type: application/json; indent=4; charset=utf-8

    {
        "msg": "success!"
    }

HTTP 400: Bad request
---------------------

Answer has errors. Details will be in the response body.

Possibilities include:

* non-existent ``survey_id``
* disabled survey
* missing required fields
* data is in the wrong format

Example curl::

    curl -v -XPOST 'https://input.mozilla.org/api/v2/hb/' \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "person_id": "c1dd81f2-6ece-11e4-8a01-843a4bc832e4",
        "survey_id": "nonexistent",
        "flow_id": "20141114_attempt2",
        "response_version": 1,
        "question_id": "howwaslunch",
        "updated_ts": 1416011156000,
        "is_test": true
    }'


yields this response::

    HTTP/1.0 400 BAD REQUEST
    <uninteresting headers omitted>
    Content-Type: application/json; indent=4; charset=utf-8

    {
        "msg": "bad request; see errors",
        "errors": {
            "survey_id": [
                "Object with name=nonexistent does not exist."
            ],
            "question_text": [
                "This field is required."
            ],
            "variation_id": [
                "This field is required."
            ]
        }
    }


Each field with errors will have its own slot in the "errors"
section. If there are multiple errors for that field, it'll show
multiple errors.


HTTP 500: Server error
----------------------

Tell Will. He has some 'splaining to do.


Examples
========

Minimal example
---------------

Anything less than this will kick up "required" type errors.

::

    curl -v -XPOST 'https://input.mozilla.org/api/v2/hb/' \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "person_id": "c1dd81f2-6ece-11e4-8a01-843a4bc832e4",
        "survey_id": "lunch",
        "flow_id": "20141117_attempt1",
        "response_version": 1,
        "question_id": "howwaslunch",
        "question_text": "how was lunch?",
        "variation_id": "1",
        "updated_ts": 1416011156000,
        "is_test": true
    }'


Example flow
------------

(I'm totally making things up here, but maybe this is what it could
look like?)

Began:

::

    curl -v -XPOST $URL \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "person_id": "c1dd81f2-6ece-11e4-8a01-843a4bc832e4",
        "survey_id": "lunch",
        "flow_id": "20141117_attempt5",
        "response_version": 1,
        "question_id": "howwaslunch",
        "updated_ts": 1416011156000,
        "question_text": "how was lunch?",
        "variation_id": "1",
        "score": null,
        "max_score": null,
        "flow_began_ts": 1416011100000,
        "flow_offered_ts": 0,
        "flow_voted_ts": 0,
        "flow_engaged_ts": 0,
        "platform": "",
        "channel": "",
        "version": "",
        "locale": "",
        "build_id": "",
        "partner_id": "",
        "profile_age": null,
        "profile_usage": {},
        "addons": {},
        "extra": {},
        "is_test": true
    }'


Voted, but not engaged, yet::

    curl -v -XPOST $URL \
        -H 'Accept: application/json; indent=4' \
        -H 'Content-type: application/json' \
        -d '
    {
        "person_id": "c1dd81f2-6ece-11e4-8a01-843a4bc832e4",
        "survey_id": "lunch",
        "flow_id": "20141117_attempt7",
        "response_version": 1,
        "question_id": "howwaslunch",
        "updated_ts": 1416011180000,
        "question_text": "how was lunch?",
        "variation_id": "1",
        "score": 5.0,
        "max_score": 10.0,
        "flow_began_ts": 1416011100000,
        "flow_offered_ts": 1416011120000,
        "flow_voted_ts": 1416011130000,
        "flow_engaged_ts": 0,
        "platform": "Windows 7",
        "channel": "stable",
        "version": "33.1",
        "locale": "en-US",
        "build_id": "e3b0971e-6ecf-11e4-af44-843a4bc832e4",
        "partner_id": "Phil, Prince of Heck",
        "profile_age": 365,
        "profile_usage": {"avgperday": "5"},
        "addons": {"count": 4, "badones": "plenty"},
        "extra": {"moonphase": "waning gibbous"},
        "is_test": true
    }'
