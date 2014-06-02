==================
 Fjord smoketests
==================

This directory holds Fjord client-based smoke tests. They're based on the
Mozilla WebQA tests at `<https://github.com/mozilla/input-tests/>`_ which
is why they're different than the rest of the code in this repository.

These tests use the following things:

1. py.test
2. pytest-mozwebqa
3. pytest-xdist
4. UnittestZero
5. selenium


Setting up to run the tests
===========================

I suggest using a different virtual environment for these tests than the
rest of Fjord so you're not mixing requirements.

1. ``mkvirtualenv fjord-smoketests``
2. ``pip install -r requirements.txt``


Running the tests
=================

Whenever you want to run these tests, first enter your virutal environment.

To run tests it's a simple case of calling ``py.test`` from the root
directory::

    py.test --driver=firefox tests

Running tests against the Input stage environment::

    py.test --driver=firefox --baseurl=https://input.allizom.org tests

Running tests against a local instance of Fjord::

    py.test --driver=firefox --baseurl=http://localhost:8000 tests

Note that to run it against a local instance, you probably need some
data so that the dashboard tests have enough data to work with to
run. You can generate some data and reindex like this::

    $ cd ..
    $ ./manage.py generatedata --with=samplesize=1000
    $ ./manage.py esreindex


.. Note::

   When giving a baseurl, make sure it doesn't have a ``/`` at the end.


For more command line options see https://github.com/davehunt/pytest-mozwebqa


Writing Tests
=============

If you want to get involved and add more tests then there's just a few
things we'd like to ask you to do:

1. Use the Mozilla WebQA `template files`_ for all new tests and page objects
2. Follow the Mozilla WebQA `style guide`_
3. Fork this project with your own GitHub account
4. Make sure all tests are passing, and submit a pull request with your changes

.. _template files: https://github.com/mozilla/mozwebqa-test-templates
.. _style guide: https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide


License
=======

This software is licensed under the `MPL`_ 2.0:

    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at http://mozilla.org/MPL/2.0/.

.. _MPL: http://www.mozilla.org/MPL/2.0/
