.. _hacking-howto-chapter:

==============================
Hacking HOWTO for Contributors
==============================


Summary
=======

This chapter helps you get a minimal installation of Fjord up and
running so as to make it easier for contributing.

If you're interested in setting up Fjord for a production
deployment, this is not the chapter for you---look elsewhere.

If you have any problems getting Fjord running, let us know. See the
:ref:`project-details`.


Operating systems
=================

Windows
-------

If you're using Windows as your operating system, you'll need to set
up a virtual machine and run Fjord in that. Fjord won't run in
Windows.

If you've never set up a virtual machine before, let us know and we
can walk you through it. Having said that, it's not easy to do for
people who haven't done it before.


Mac OSX
-------

Just follow along with the instructions below. Several of us use OSX,
so if you run into problems, let us know.


Linux
-----

We know these work in Debian Testing (Wheezy) and will probably work
in Debian derivatives like Ubuntu. It's likely that you'll encounter
some steps that are slightly different. If you run into problems, let
us know.


Requirements
============

For the minimum installation, you'll need the following:

* git
* Python 2.6 or 2.7
* `pip <http://www.pip-installer.org/en/latest/>`_
* MySQL server and client headers
* Memcached Server

Installation for these is very system dependent. Using a package
manager, like yum, aptitude, or brew, is encouraged.


Getting the Source
==================

Grab the source from Github using::

    $ git clone --recursive git://github.com/mozilla/fjord.git
    $ cd fjord

.. Note::

   If you forgot to add ``--recursive``, you can get all the
   submodules with::

       $ git submodule update --init --recursive


Installing dependencies
=======================

Compiled Packages
-----------------

There are a small number of packages that need compiling, including the MySQL
Python client.

You can install these either with your system's package manager or
with ``pip``.

To use pip, do this::

    $ sudo pip install -r requirements/compiled.txt

If you want to use your system's package manager, you'll need to go
through ``requirements/compiled.txt`` and install the dependencies by
hand.


Python Packages
---------------

All the pure-Python requirements are provided in the "vendor library"
which is the ``fjord/vendor`` and ``fjord/vendor-local`` directories.

This makes the packages available to Python without installing them
globally and keeps them pinned to known-compatible versions.

See the :ref:`vendor library <vendor-chapter>` documentation for more
information on getting the vendor library, adding things to it, and
keeping it up to date.


.. _hacking-howto-db:

Set up the database
===================

We need to create a database user and a database table. These
instructions assume you use:

:database: fjord
:username: fjord
:password: password

In a terminal, do::

    $ mysql -u root -p
    mysql> CREATE DATABASE fjord;
    mysql> create user 'fjord'@'localhost' IDENTIFIED BY 'password';
    mysql> GRANT ALL ON fjord.* TO 'fjord'@'localhost';


.. Note::

   If you use different values, make sure to substitute your values in the
   correct places in the rest of the instructions.


.. _hacking-howto-configuration:

Configuration
=============

Copy the file ``local.py-dist`` in the ``fjord/settings`` directory to
``local.py``, and edit it to fit your needs. In particular, you should:

* Set the database options to fit what you configured above in ``DATABASES``.
* Fill in a value for ``SECRET_KEY``. This should be some random string. It
  will be used to seed hashing algorithms.
* Fill in a value for ``HMAC_KEYS``. This should also be a random string, the
  longer the better. It is used as a sort of 'pepper' analagous to the password
  salt. Not supplying this will make cause user generation to fail.
* Set ``CELERY_ALWAYS_EAGER = False``, which allows running Fjord without
  running Celery---all tasks will be done synchronously.
* Set ``SESSION_COOKIE_SECURE = False``, unless you plan on using https.

Now you can copy and modify any settings from ``settings/base.py`` into
``settings/local.py`` and the value will override the default.

.. Note::

    These instructions are to set up a development environment; more care
    should be taken in production.


Memcached
---------

Make sure you have Memcached running; it is used for caching database queries.

An easy way to flush the cache if things are going funny is like this::

   echo "flush_all" | nc localhost 11211

Assuming you have Memcached configured to listen to 11211.


LESS
----

To install LESS you will first need to `install Node.js and NPM
<https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Now install LESS using::

    $ sudo npm install less

Ensure that lessc (might be located at /usr/lib/node_modules/less/bin) is
accessible on your PATH.


.. _hacking-howto-schemas:

Database Schemas
----------------

Note the two settings ``TEST_CHARSET`` and ``TEST_COLLATION``. Without
these, the test suite will use MySQL's (moronic) defaults when
creating the test database (see below) and lots of tests will
fail. Hundreds.

For details on how to create the database, see :ref:`hacking-howto-db`.

Fjord uses `South <http://south.aeracode.org>`_ for database
migrations. To get an initial database set up, run::

    $ ./manage.py syncdb         # To get South ready
    $ ./manage.py migrate --all  # To run the initial migrations


You'll now have an empty but up-to-date database!

Finally, you'll probably want to create a superuser. Just use Django's
``createsuperuser`` management command::

    $ ./manage.py createsuperuser

and follow the prompts.


Product Details Initialization
------------------------------

One of the packages Fjord uses, ``product_details``, needs to fetch
JSON files containing historical Firefox version data and write them
within its package directory. To set this up, run this command to do
the initial fetch::

    $ ./manage.py update_product_details


Testing it out
==============

To start the dev server, run ``./manage.py runserver``, then open up
``http://localhost:8000``.

If everything's working, you should see a somewhat empty version of
the Input home page!


.. _setting-up-tests:

Setting up the tests
--------------------

Let's do the setup required for running tests.

You'll need to add an extra grant in MySQL for your database user::

    $ mysql -u root -p
    mysql> GRANT ALL ON test_NAME.* TO USER@localhost;

Where ``NAME`` and ``USER`` are the same as the values in your
database configuration.

The test suite will create and use this database, to keep any data in
your development database safe from tests.

Running the test suite is easy::

    $ ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the :ref:`test documentation
<tests-chapter>`.


Advanced install
================

After reading the above, you should have everything you need for a
minimal working install which lets you run Fjord and work on many
parts of it.

However, it's missing some components. See
:ref:`advanced-installation-chapter` for everything else.
