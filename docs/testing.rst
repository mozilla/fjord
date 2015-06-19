.. _tests-chapter:

================
Testing in Fjord
================

Tests in Fjord allow us to make changes and be reasonably sure that
the system continues to work. Further, they make it easier to verify
correctness for behavioral details.


.. Note::

   We use the ``py.test`` script in the root directory rather than the
   one installed with py.test in PATH. We need it to set up the path
   because we have many of the libraries in ``vendor/``. Once we get
   rid of ``vendor/`` we can use the regular ``py.test`` script.


Running tests
=============

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
=================

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


Writing New JavaScript Tests
============================

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


Changing tests
==============

Unless the current behavior, and thus the test that verifies that
behavior is correct, is demonstrably wrong, don't change tests. Tests
may be refactored as long as its clear that the result is the same.


Removing tests
==============

On those rare, wonderful occasions when we get to remove code, we
should remove the tests for it, as well.

If we liberate some functionality into a new package, the tests for
that functionality should move to that package, too.
