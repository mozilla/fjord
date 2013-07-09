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

To run the test suite, do::

    $ ./manage.py test

However, that doesn't provide the most sensible defaults. Here is a
good command to alias to something short::

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

* Many models have "modelmakers" which are easier to work with for
  some kinds of tests than fixtures. For example,
  ``forums.tests.document`` is the model maker for
  ``forums.models.Document``.


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


In-Suite Selenium Tests
=======================

Front end testing that can't be done with QUnit can be done with
Selenium_, a system for remote-controlling real browser windows and
verifying behavior. Currently the tests are hard coded to use a local
instance of Firefox.

.. _Selenium: http://docs.seleniumhq.org/

These tests are designed to be run locally on development laptops and
locally on Jenkins. They are to provide some more security that we
aren't breaking things when we write new code, and should run before
commiting to master, just like any of our other in-suite tests. They
are not intended to replace the QA test suites that run against dev,
stage, and prod, and are not intended to beat on the site to find
vulnerabilities.

You don't need a Selenium server to run these, and don't need to
install anything more than a modern version of Firefox, and the
dependencies in the vendor library.

These tests use Django's `Live Server TestCase`_ class as a base,
which causes Django to run a real http server for some of it's tests,
instead of it's mocked http server that is used for most tests. This
means it will allocate a port and try to render pages like a real
server would.  If static files are broken for you, these tests will
likely fail as well.

.. _`Live Server TestCase`: https://docs.djangoproject.com/en/1.4/topics/testing/#django.test.LiveServerTestCase


Running Selenium Tests
----------------------

By default, the Selenium tests will run as a part of the normal test
suite. When they run, a browser window will open and steal input for a
moment. You don't need to interact with it, and if all goes well, it
will close when the tests are complete. This cycle of open/test/close
may happen more than once each time you run the tests, as each
TestCase that uses Selenium will open it's own webdriver, which opens
a browser window.


Writing Selenium Tests
----------------------

To add a Selenium test, subclass
``kitsune.sumo.tests.SeleniumTestCase``.  instance of Selenium's
webdriver will be automatically instantiated and is available at
``self.webdriver``, and you can do things like
``self.webdriver.get(url)`` and
``self.webdriver.find_element_by_css_selector('div.baz')``. For more
details about how to work with Selenium, you can check out Selenium
HQ's guide_.

.. _guide: http://docs.seleniumhq.org/docs/03_webdriver.jsp


XVFB and Selenium
-----------------

Because Selenium opens real browser windows, it can be kind of
annoying as windows open and steal focus and switch
workspaces. Unfortunatly, Firefox doesn't have a headless mode of
operation, so we can't simply turn off the UI. Luckily, there is a way
to work around this fairly easily on Linux, and with some effort on
OSX.

Linux
~~~~~

Install XVFB_ and run the tests with it's xvfb-run binary. For
example, if you run tests like::

    ./manage.py test -s --noinput --logging-clear-handlers


You can switch to this to run with XVFB::

    xvfb-run ./manage.py test -s --noinput --logging-clear-handlers


This creates a virtual X session for Firefox to run in, and sets up
all the fiddly environment variables to get this working well. The
tests will run as normal, and no windows will open, if all is working
right.

OSX
~~~

The same method can be used for OSX, but it requires some fiddliness.
The default version of Firefox for OSX does not use X as it's
graphic's backend, so by default XVFB can't help. You can however run
an X11 enabled version of OSX and a OSX version of XVFB. You can find
more details `here
<http://afitnerd.com/2011/09/06/headless-browser-testing-on-mac/>`_.

.. Note::

   I don't use OSX, and that blog article is fairly out of date. If
   you find a way to get this working bettter or easier, or have
   better docs to share, please do!
