======================
 Smoketests for Fjord
======================

Summary
=======

This directory holds a set of Selenium-based smoketests for Input. These tests require a web-server to run against. You can 
This is based in large part on the mozwebqa code, but it's slimmed
down for the bits we need. This makes it easier to copy code back and
forth between these smoketests and the input-tests repository.

* https://github.com/davehunt/pytest-mozwebqa
* https://github.com/mozilla/input-tests

Setting up
==========

First, you need the requirements::

    $ pip install -r requirements.txt


Running tests
=============

First, you need an environment to run against. If you're running
against localhost, then you need to be running fjord in another
window.

If you're running against stage, you need to set
``BASE_URL=https://input.allizom.org/`` in your environment variables.

If you're running against production (do **NOT** run in destructive
mode), you need to set ``BASE_URL=https://input.mozilla.org/`` in your
environment variables.

These tests use nose as the test collector and runner.

To run the tests, do::

    $ nosetests

This runs all non-destructive tests with the default configuration.

To set various test-related bits, you need to use environment
variables. The following variables do things:

BASE_URL
    The url to run against.

    Defaults to ``http://localhost:8000``

DESTRUCTIVE
    Whether (1) or not (0) to run destructive tests.

    Defaults to ``0`` which means no destructive tests will run.

    .. Warning::

       Don't run destructive tests against production!

DRIVER
    Which Selenium webdriver to use.

    Defaults to ``firefox``.

    .. Note::

       The smoketests don't support other drivers right now.

FIREFOX_PATH
    The path to the Firefox binary.

    Defaults to None.

PROFILE_PATH
    The path for the Firefox profile.

    Defaults to None.

TIMEOUT
    The timeout in seconds for page loads.

    Defaults to ``60``.


For example, to run destructive tests with a timeout of 5 seconds
against stage, you'd do:

    BASE_URL=https://input.allizom.org/ TIMEOUT=5 DESTRUCTIVE=1 nosetests


Writing tests
=============

All tests should subclass ``tests.BaseTestCase``. This gives you all
the Selenium setup/teardown.

If your test is not destructive, you need to use the
``@tests.nondestructive`` decorator. By default, all tests are assumed
to be destructive and will not run unless ``DESTRUCTIVE=1`` is in the
environment.

Test cases should be easy to read. Most of the "business logic" of
identifying items on the page, manipulating things on the page and
navigating pages should be in the ``pages/`` code.
