.. _hacking-howto-chapter:

==============================
Hacking HOWTO for Contributors
==============================


Summary
=======

This chapter helps you get a minimal installation of Fjord up and
running so as to make it easier for contributing.

If you're interested in setting up Fjord for a production deployment,
this is not the chapter for you---look elsewhere.

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
* lessc

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

There are a small number of packages that need compiling, including
the MySQL Python client.

You can install these either with your system's package manager or
with ``pip``.

To use pip, do this::

    $ sudo pip install -r requirements/compiled.txt

If you want to use your system's package manager, you'll need to go
through ``requirements/compiled.txt`` and install the dependencies by
hand.

**OSX Mountain Lion**: One of the things in
``requirements/compiled.txt`` is MySQL Python library.  If you're
using OSX Mountain Lion, then
`<http://stackoverflow.com/questions/11787012/how-to-install-mysqldb-on-mountain-lion>`_
should help you install it.
In addition, if you encounter an error stating ``Library not loaded: libmysqlclient.18.dylib``, then
`<http://stackoverflow.com/questions/6383310/python-mysqldb-library-not-loaded-libmysqlclient-18-dylib>`_
explains how to fix this.


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

.. Note::

   If you use different values, make sure to substitute your values in
   the correct places in the rest of the instructions.


In a terminal, do::

    $ mysql -u root -p
    mysql> CREATE DATABASE fjord;
    mysql> create user 'fjord'@'localhost' IDENTIFIED BY 'password';
    mysql> GRANT ALL ON fjord.* TO 'fjord'@'localhost';


.. _hacking-howto-configuration:

Configuration
=============

Copy the file ``local.py-dist`` in the ``fjord/settings`` directory to
``local.py``, and edit it to fit your needs. In particular, you
should:

* Set the database options to fit what you configured above in
  ``DATABASES``.
* Fill in a value for ``SECRET_KEY``. This should be some random
  string. It will be used to seed hashing algorithms.
* Fill in a value for ``HMAC_KEYS``. This should also be a random
  string, the longer the better. It is used as a sort of 'pepper'
  analagous to the password salt. Not supplying this will make cause
  user generation to fail.
* Set::

      SESSION_COOKIE_SECURE = False

  unless you plan on using https.
* Set ``SITE_URL`` to the protocol, host and port you're going to run
  your fjord instance on. By default, when you type::

      ./manage.py runserver

  it launches the server on ``http://127.0.0.1:8000``. If you're going
  to do that, set::

      SITE_URL = 'http://127.0.0.1:8000'


Now you can copy and modify any settings from
``fjord/settings/base.py`` and
``vendor/src/funfactory/funfactory/settings_base.py`` into
``fjord/settings/local.py`` and the value will override the default.

.. Warning::

   These instructions are to set up a development environment; more
   care should be taken in production.


Cache
-----

Cache is optionally configured with the ``CACHES`` setting in your
``fjord/settings/local.py`` settings file..

If you're running a developer environment, you can add the default
``CACHES`` settings to the file. It probably will look like this::

    CACHES = {
        'default': {
            'LOCATION': '',
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
            }
        }


It's better to use memcached since that's closer to what we run in
production. Here's a sample ``CACHES`` setting which assumes you're
running memcached at port 11211 on localhost::

    CACHES = {
        'default': {
            'BACKEND': 'caching.backends.memcached.CacheClass',
            'LOCATION': 'localhost:11211',
            'TIMEOUT': 600,
            'KEY_PREFIX': 'fjord'
            }
        }


.. Note::

   If you're using memcached, an easy way to flush the cache if things
   are going funny is like this::

       echo "flush_all" | nc localhost 11211

   Assuming you have memcached configured to listen to 11211 on
   localhost.


LESS
----

To install LESS you will first need to `install Node.js and NPM
<https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Now install LESS using::

    $ sudo npm install less

Make sure that ``lessc`` is available on your path. NPM probably
installed it to ``node_modules/less/bin/lessc`` and
``node_modules/.bin/lessc``.

LESS files are automatically converted by `jingo-minify
<https://github.com/jsocol/jingo-minify>`_.


.. _hacking-howto-schemas:

Database Schemas
----------------

For instructions on how to create the database, see
:ref:`hacking-howto-db`.

Fjord uses `South <http://south.aeracode.org>`_ for database
migrations.  To get an initial database set up, run::

    $ ./manage.py syncdb         # To get South ready
    $ ./manage.py migrate --all  # To run the initial migrations


You'll now have an empty but up-to-date database!

Finally, if you weren't asked to create a superuser and created one
already, you'll probably want to create a superuser. Just use Django's
``createsuperuser`` management command::

    $ ./manage.py createsuperuser

and follow the prompts.

.. Note::

   Fjord uses `Persona <https://login.persona.org/>`_ for
   authentication. When you log into your local fjord instance, you'll
   be using the email address that you set up with
   ``createsuperuser``.

   Make sure it's a valid email address that you have set up with
   Persona.


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
``http://127.0.0.1:8000``.

If everything's working, you should see a somewhat empty version of
the Input home page!


.. _setting-up-tests:

Setting up the tests
--------------------

Let's do the setup required for running tests.

You'll need to add an extra grant in MySQL for your database user::

    $ mysql -u root -p
    mysql> GRANT ALL ON test_fjord.* TO fjord@localhost;

.. Note::

   If you used different values, make sure to substitute your values
   in the correct places in the rest of the instructions.

The test suite will create and use this database, to keep any data in
your development database safe from tests.

Running the test suite is easy::

    $ ./manage.py test -s --noinput --logging-clear-handlers

For more information, see the :ref:`test documentation
<tests-chapter>`.


Getting sample data
===================

You can get sample data in your db by running::

    $ ./manage.py generatedata

This will generate 5 happy things and 5 sad things so that your Fjord
instance has something to look at.

If you want to generate a lot of random sample data, then do::

    $ ./manage.py generatedata --with=samplesize=1000

That'll generate 1000 random responses. You can re-run that and also
pass it different amounts. It'll generate random sample data starting
at now and working backwards.


Advanced install
================

After reading the above, you should have everything you need for a
minimal working install which lets you run Fjord and work on many
parts of it.

However, it's missing some things:

* locales: See :ref:`l10n-chapter` for details.
* ElasticSearch: See :ref:`es-chapter` for details.


Troubleshooting
===============

Criminy! I can't get this damn Persona login working!
-----------------------------------------------------

When you log in, do you end up on the dashboard page, but not logged
in?

Are you seeing a "misconfigured" error?

If so, make sure you have the following set in
``fjord/settings/local.py``::

    DEBUG = True

    # The value should be a non-empty string.
    SECRET_KEY = 'some secret key'

    # The value should be the protocol, host, and port that you use
    # to access the site. If this doesn't match, then you'll get
    # a "misconfigured" error.
    SITE_URL = 'http://127.0.0.1:8000'

    SESSION_COOKIE_SECURE = False


See `the django-browserid troubleshooting docs
<https://django-browserid.readthedocs.org/en/latest/details/troubleshooting.html>`_
for more details.
