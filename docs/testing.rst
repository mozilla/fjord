.. _tests-chapter:

================
Testing in Fjord
================

Tests in Fjord allow us to make changes and be reasonably sure that
the system continues to work. Further, they make it easier to verify
correctness for behavioral details.


Setting up the tests
====================

To set up the tests, follow the instructions in
:ref:`setting-up-tests`.


Running tests
=============

Running tests and arguments
---------------------------

The tests have LiveServerTestCase tests that use Selenium to do ui
testing now. Before you run the tests, you have to run these two
commands::

    $ ./manage.py collectstatic
    $ ./manage.py compress_assets


To run the test suite, do::

    $ ./manage.py test


However, that doesn't provide the most sensible defaults. Amongst
other things, you see tons and tons and tons and tons and tons and
tons and tons and tons and tons and tons and tons and tons and tons of
debugging output. Ew.

I suggest you run it this way::

    $ ./manage.py test -s --noinput --logging-clear-handlers


The ``-s`` flag is important if you want to be able to drop into PDB
from within tests.

Some other helpful flags are:

``-x``:
  Fast fail. Exit immediately on failure. No need to run the whole
  test suite if you already know something is broken.

``--pdb``:
  Drop into PDB on an uncaught exception. (These show up as ``E`` or
  errors in the test results, not ``F`` or failures.)

``--pdb-fail``:
  Drop into PDB on a test failure. This usually drops you right at the
  assertion.


The test suite will create a new database named ``test_%s`` where
``%s`` is whatever value you have for
``settings.DATABASES['default']['NAME']``.

When the schema changes, you may need to drop the test database. You
can also run the test suite with ``FORCE_DB`` once to cause Django to
drop and recreate it::

    $ FORCE_DB=1 ./manage.py test -s --noinput --logging-clear-handlers


Running specific tests
----------------------

You can run part of the test suite by specifying the directories of the
code you want to run, like::

    $ ./manage.py test fjord/feedback/tests

You can specify specific tests::

    # ./manage.py test fjord.feedback.tests.test_ui:TestFeedback.test_happy_url

See the output of ``./manage.py test --help`` for more arguments.


Running tests with Xvfb
-----------------------

Because Selenium opens real browser windows, it can be kind of
annoying as windows open and steal focus and switch
workspaces. Unfortunatly, Firefox doesn't have a headless mode of
operation, so we can't simply turn off the UI. Luckily, there is a way
to work around this fairly easily on Linux, and with some effort on
OSX.


On Linux:

    Install Xvfb and run the tests with it's xvfb-run binary. For
    example, if you run tests like::

        ./manage.py test -s --noinput --logging-clear-handlers


    You can switch to this to run with Xvfb::

        xvfb-run ./manage.py test -s --noinput --logging-clear-handlers


    This creates a virtual X session for Firefox to run in, and sets
    up all the fiddly environment variables to get this working
    well. The tests will run as normal, and no windows will open, if
    all is working right.


On OSX:

    The same method can be used for OSX, but it requires some
    fiddliness.  The default version of Firefox for OSX does not use X
    as it's graphic's backend, so by default Xvfb can't help. You can
    however run an X11 enabled version of OSX and a OSX version of
    Xvfb. You can find more details `here
    <http://afitnerd.com/2011/09/06/headless-browser-testing-on-mac/>`_.

    .. Note::

       I don't use OSX, and that blog article is fairly out of
       date. If you find a way to get this working bettter or easier,
       or have better docs to share, please do!


Writing New Tests
=================

Code should be written so it can be tested, and then there should be
tests for it.

When adding code to an app, tests should be added in that app that
cover the new functionality. All apps have a ``tests`` module where
tests should go. They will be discovered automatically by the test
runner as long as the look like a test.

* Avoid naming test files ``test_utils.py``, since we use a library
  with the same name. Use ``test__utils.py`` instead.

* If you're expecting ``reverse`` to return locales in the URL, use
  ``LocalizingClient`` instead of the default client for the
  ``TestCase`` class.

* We use modelmakers instead of fixtures. For example,
  ``fjord.feedback.tests.response`` is the modelmaker for
  ``fjord.feedback.models.Response``.

* To add a Selenium test, subclass
  ``fjord.base.tests.SeleniumTestCase``. The instance of Selenium's
  webdriver will be automatically instantiated and is available at
  ``self.webdriver``, and you can do things like
  ``self.webdriver.get(url)`` and
  ``self.webdriver.find_element_by_css_selector('div.baz')``. For more
  details about how to work with Selenium, you can check out Selenium
  HQ's guide_.

.. _guide: http://docs.seleniumhq.org/docs/03_webdriver.jsp


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
