.. _tests-chapter:

================
Testing in Fjord
================

Tests in Fjord allow us to make changes and be reasonably sure that
the system continues to work. Further, they make it easier to verify
correctness for behavioral details.


.. contents::


Unit tests
==========

.. Note::

   We use the ``py.test`` script in the root directory rather than the
   one installed with py.test in PATH. We need it to set up the path
   because we have many of the libraries in ``vendor/``. Once we get
   rid of ``vendor/`` we can use the regular ``py.test`` script.


Setup
-----

Before you run the tests, you have to run the ``collectstatic`` command. This
compiles LESS files to CSS files and creates the bundles that some of
the tests require to run. If you don't do this, then a few of the
tests will fail.

To run collectstatic, do::

    ./manage.py collectstatic

You don't have to do this often. I'd do it the first time and then any
time you run the tests with a fresh db.

FIXME: This is annoying and it'd be nice to get it fixed.


Running tests and arguments
---------------------------

To run the test suite, do::

    ./py.test


Default options for running the test are in ``pytest.ini``. This is a
good set of defaults.

If you ever need to change the defaults, you can do so at the command
line.

Helpful command-line arguments:

``--pdb``:
  Drop into pdb on test failure.

``--create-db``:
  Create a new test database.

``--showlocals``:
  Shows local variables in tracebacks on errors.

``--exitfirst``:
  Exits on the first failure.

See ``./py.test --help`` for more arguments.


The test suite will create a new database named ``test_%s`` where
``%s`` is whatever value you have for
``settings.DATABASES['default']['NAME']``.


Running specific tests
----------------------

There are a bunch of ways to specify a subset of tests to run:

* only tests marked with the 'es_tests' marker::

    ./py.test -m es_tests

* all the tests but those marked with the 'es_tests' marker::

    ./py.test -m "not es_tests"

* all the tests but the suggests ones::

    ./py.test --ignore fjord/suggests

* all the tests that have "foobar" in their names::

    ./py.test -k foobar

* all the tests that don't have "foobar" in their names::

    ./py.test -k "not foobar"

* tests in a certain directory::

    ./py.test fjord/suggest/

* specific test::

    ./py.test fjord/suggest/tests/test_dummy.py::DummySuggesterTestCase::test_get_suggestions

See http://pytest.org/latest/usage.html for more examples.


Writing New Tests
-----------------

Code should be written so it can be tested, and then there should be
tests for it.

When adding code to an app, tests should be added in that app that
cover the new functionality. All apps have a ``tests`` module where
tests should go. They will be discovered automatically by the test
runner as long as the look like a test.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the
  ``TestCase`` class.

* We use FactoryBoy to generate model instances instead of using fixtures.
  ``fjord.feedback.tests.ResponseFactory`` generates
  ``fjord.feedback.models.Response`` instances.

* To add a smoketest, see the ``README.rst`` file in the ``smoketests/``
  directory.


JavaScript Tests
================

JavaScript tests are not run in our normal unit test suite. Instead we have
a different test system.

We test JavaScript utility functions using `QUnit <http://qunitjs.com/>`_.

These tests are located in ``fjord/base/static/tests/``.


Running tests
-------------

Launch the server with::

    ./manage.py runserver

Then go to::

    http://127.0.0.1:8000/static/tests/index.html

(You might have to use a different protocol, host and port depending
on how you have Fjord set up.)


Adding tests
------------

To add a new test suite, add a couple of ``script`` lines to ``index.html`` in
the relevant place and then create a new ``test_FILENAMEHERE.js`` file
with your QUnit tests.


Smoketests
==========

We have a smoketest suite. For more details, see that README:

https://github.com/mozilla/fjord/tree/master/smoketests


Comprehensive test plan
=======================

Sometimes, we need to make substantive changes to the site that touch a lot of
parts. This test plan covers all the things you should do (at a minimum) to make
sure those parts are still working.

This is a good thing to do after doing a Django upgrade.

.. Note::

   These tests aren't run frequently and they're probably out of date.

   Run through the test plan with your code **before** you make your
   changes and update parts that have changed. Make sure to add
   sections for new functionality.

.. Note::

   This is labeled "comprehensive", but probably leave some stuff out. We should
   improve it as we use it.

.. Note::

   This test plan is very terse. You'll need to know your way around Fjord and
   Input for this to make a lot of sense. Sorry about that.


Unit tests
----------

1. run ``./py.test`` to run the unit tests with a clean database


Smoketests
----------

1. run ``./manage.py runserver`` in one terminal and launch the smoketests
   in another terminal


Testing collectstatic
---------------------

1. delete everything in ``static/``
2. run ``./manage.py collectstatic`` and verify no errors and ``.js`` and ``.css``
   files got built


Testing migrations
------------------

1. run ``./manage.py makemigrations`` -- it shouldn't create any new
   migrations
2. run ``./manage.py migrate`` with a db dump


Django check
------------

1. run ``./manage.py check`` and verify no errors


Testing Elasticsearch and indexing
----------------------------------

1. run ``./manage.py esstatus``
2. run ``./manage.py esreindex --percent=5`` to create a new index and
   index some stuff
3. run ``./manage.py esstatus`` to make sure the new index is there
4. run ``./manage.py esdelete <index>`` to delete that index
5. run ``./manage.py esstatus`` to make sure the index was created
6. run ``./manage.py esreindex --percent=5`` to recreate the index
7. verify feedback is indexed

   1. run ``./manage.py runserver`` to launch the server
   2. open up a browser
   3. create some feedback and verify it appears on the front page
      dashboard
   4. run some searches in the dashboard to make sure searches work

8. verify reindexing works from admin:

   1. make sure ``CELERY_ALWAYS_EAGER = False`` in
      ``fjord/settings/local.py``
   2. run ``./manage.py celeryd`` to launch celery server
   3. in another terminal, run ``./manage.py runserver``
   4. open up a browser
   5. log in to the server
   6. go to admin
   7. go to *Elasticssearch maintenance*
   8. launch a reindexing

      Make sure it's reindexing things. Once you know it's reindexing
      things, then you can cut it short. Otherwise it takes *forever.


Testing localizations
---------------------

1. make sure your ``locale/`` directory is up to date
2. run ``./manage.py extract`` and make sure that it produced or updated
   a ``locale/templates/LC_MESSAGES/django.pot`` file and that msgids
   did not change
3. run ``./manage.py merge`` and make sure it did the right thing
4. run ``./bin/compile-linted-mo.sh`` and make sure dennis linted the
   ``.po`` files and that the script compiled ``.mo`` files
5. verify that localizations work:

   1. run ``./manage.py runserver`` to launch the server
   2. open up a browser
   3. go to the front page dashboard and look at it in French and make
      sure all strings are translated
   4. leave feedback and make sure feedback form is in French


Testing analyzer section
------------------------

Verify analyzer views load:

1. run ``./manage.py runserver`` to launch the server
2. open up a browser
3. log in to the server
4. go to analyzer section
5. make sure all the views load


Testing admin
-------------

Verify the admin views load:

1. run ``./manage.py runserver`` to launch the server
2. open up a browser
3. log in to the server
4. go to admin
5. make sure all the admin views load


Testing cron jobs
-----------------

1. for each job in ``bin/crontab/crontab.tpl``, make sure it works


Testing vagrant
---------------

With an existing vagrant environment:

1. run ``vagrant up``
2. run ``./peep.sh install -r requirements/requirements.txt``
3. run ``./peep.sh install -r requirements.dev.txt``
4. run ``vagrant ssh``

   1. run ``cd fjord``
   2. run ``./py.test``

Now we're going to create a new vagrant environment:

1. run ``vagrant halt``
2. run ``vagrant destroy --force``
3. run ``vagrant up``
4. run ``vagrant ssh``

   1. run ``cd fjord``
   2. run ``./py.test``

If that works, then it probably works fine in vagrant development
environment.
