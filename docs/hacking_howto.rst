.. _hacking-howto-chapter:

==================================================
Hacking HOWTO for Contributors: Install, run, test
==================================================

.. contents::
   :local:


Summary
=======

This chapter covers getting Fjord set up locally, running tests and
some other basic things to make it easier for contributing.

If you're interested in setting up Fjord for a production deployment,
this is not the chapter for you---look elsewhere.

If you have any problems getting Fjord running, let us know. See the
:ref:`overview`.


Installing
==========

**Windows**

    If you're using Windows as your operating system, you'll need to
    set up a virtual machine with Linux and run Fjord in that. Fjord
    won't run on Windows.

    If you've never set up a virtual machine before, let us know and
    we can walk you through it. Having said that, it's not easy to do
    for people who haven't done it before.


**Mac OSX**

    Just follow along with the instructions below. Several of us use
    OSX, so if you run into problems, let us know.

    If worse comes to worse, you can set up a virtual machine with
    Linux and follow those instructions.


**Linux**

    We know these work in Debian Testing (Wheezy) and will probably
    work in Debian derivatives like Ubuntu. It's likely that you'll
    encounter some steps that are slightly different. If you run into
    problems, let us know.

    Will was using Debian Testing, but is now using Fedora 20. Mike is
    using Arch.


Requirements
------------

You'll need the following installed on your system:

* git
* Python 2.6 or 2.7
* Python development headers for the version of Python you're using
* `virtualenv <https://virtualenv.pypa.io/en/latest/>`_
* `pip <https://pip.pypa.io/en/latest/>`_
* MySQL or Mariadb

  * the server
  * the client development headers

* `lessc <http://lesscss.org/>`_ -- see :ref:`hacking-howto-less`
* Elasticsearch 0.90.10 (see section on Elasticsearch)
* (optional) Memcached server -- see :ref:`hacking-howto-cache`


Installation for these is very system dependent. Using a package
manager, like yum, aptitude, or brew, is encouraged.
    
FIXME: Add package listing for Debian and Fedora here.


Getting the Fjord Source
------------------------

Grab the source from Github using::

    $ git clone --recursive git://github.com/mozilla/fjord.git
    $ cd fjord

.. Note::

   If you forgot to add ``--recursive``, you can later get all the
   submodules with::

       $ git submodule update --init --recursive


Creating a virtual environment
------------------------------

First create a Python virtual environment so that you don't have to
install Python packages system-wide.

In the Fjord repository directory, do::

    $ virtualenv venv


This creates a virtual environment in the directory ``venv/``.

Every time you go to run Fjord commands, you'll need to activate your
virtual environment. You can do that like this::

    $ source venv/bin/activate


Installing dependencies
-----------------------

Compiled Packages
~~~~~~~~~~~~~~~~~

There are a small number of packages that need compiling, including
the MySQL Python client.

Install the compiled dependencies using ``pip``::

    $ pip install -r requirements/compiled.txt


.. Note::

   If you're using OSX Mountain Lion, you'll have problems compiling
   the MySQL Python library.  See
   `<http://stackoverflow.com/questions/11787012/how-to-install-mysqldb-on-mountain-lion>`_
   for help.

   In addition, if you encounter an error stating ``Library not
   loaded: libmysqlclient.18.dylib``, then
   `<http://stackoverflow.com/questions/6383310/python-mysqldb-library-not-loaded-libmysqlclient-18-dylib>`_
   explains how to fix this.


Python Packages
~~~~~~~~~~~~~~~

All the pure-Python requirements are provided in the "vendor library"
in the ``vendor/`` directory.

This makes the packages available to Python without installing them
globally and keeps them pinned to known-compatible versions.

See the :ref:`vendor library <vendor-chapter>` documentation for more
information on getting the vendor library, adding things to it, and
keeping it up to date.


.. _hacking-howto-db:

Set up the database
-------------------

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
    mysql> CREATE DATABASE fjord CHARACTER SET utf8 COLLATE utf8_unicode_ci;
    mysql> create user 'fjord'@'localhost' IDENTIFIED BY 'password';
    mysql> GRANT ALL ON fjord.* TO 'fjord'@'localhost';


After that, do this to set up everything for the test environment::

    $ mysql -u root -p
    mysql> GRANT ALL ON test_fjord.* TO `fjord`@`localhost`;


.. _hacking-howto-configuration:

Configuration
-------------

First copy the template::

    $ cp fjord/settings/local.py-dist fjord/settings/local.py

Then edit ``fjord/settings/local.py`` to fit your system. In
particular, you should:

1. Set the ``DATABASES`` to match how you configured your database.

2. Fill in a value for ``SECRET_KEY``. This should be some random
   string. It will be used to seed hashing algorithms. If you're
   feeling unimaginative, use the elite secret string: "when ricky
   goes on pto, everything catches on fire".

3. Fill in a value for ``HMAC_KEYS``. This should also be a random
   string, the longer the better. It is used as a sort of 'pepper'
   analagous to the password salt. Not supplying this will make cause
   user generation to fail.

4. Set ``SITE_URL`` to the protocol, host and port you're going to run
   your fjord instance on. By default, when you type::

       ./manage.py runserver

   it launches the server on ``http://127.0.0.1:8000``. If you're going
   to use that then set::

       SITE_URL = 'http://127.0.0.1:8000'

5. Read through the rest of ``fjord/settings/local.py`` for things you
   should change.


After you finish with that, you should be all set.

.. Note::

   The settings in ``fjord/settings/local.py`` override default
   settings in ``fjord/settings/base.py`` and
   ``vendor/src/funfactory/funfactory/settings_base.py``. So if you
   find you need to change other things, you can look at those files
   for information.


.. _hacking-howto-less:

Setting up LESS
---------------

To install LESS you will first need to `install Node.js and NPM
<https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_.

Install LESS site-wide this way::

    $ sudo npm install less

Or alternatively, install it locally this way::

    $ npm install less

Make sure that ``lessc`` is available on your path. NPM probably
installed it to ``node_modules/less/bin/lessc`` and
``node_modules/.bin/lessc``.

If it's not, add::

    # to find the path type 'which lessc' in a terminal
    LESS_BIN = '/path/to/lessc'

to your ``fjord/settings/local.py`` file.

LESS files are automatically converted by `jingo-minify
<https://github.com/jsocol/jingo-minify>`_.

.. Note::

   If you try to run fjord, but don't have lessc installed
   or fjord looks for lessc in the wrong place, you may have
   to do this so that the .css files get regenerated::

       $ rm static/css/*.css


.. _hacking-howto-cache:

Cache (optional)
----------------

Cache is optionally configured with the ``CACHES`` setting in your
``fjord/settings/local.py`` settings file..

``CACHES`` uses the Django defaults if you haven't set it.

In production, we use memcached. If you want a system that's closer to
what we have in production, set ``CACHES`` in
``fjord/settings/local.py`` to something like this::

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': 'localhost:11211',
            'KEY_PREFIX': 'fjord'
            }
        }


Actual configuration depends on your system and how you have memcached
installed and configured.

.. Note::

   If you're using memcached, an easy way to flush the cache if things
   are going funny is like this::

       echo "flush_all" | nc localhost 11211

   Assuming you have memcached configured to listen to 11211 on
   localhost.


.. _hacking-howto-schemas:

Setting up the database tables and data and superuser
-----------------------------------------------------

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


.. _hacking-howto-es:

Setting up Elasticsearch
------------------------

Installing
~~~~~~~~~~

There's an installation guide on the ElasticSearch site:

http://www.elasticsearch.org/guide/reference/setup/installation.html

Use version 0.90.10:

http://www.elasticsearch.org/downloads/0-90-10/

The directory you install Elastic in will hereafter be referred to as
``ELASTICDIR``.

Start Elastic Search by::

    $ ELASTICDIR/bin/elasticsearch

That launches ElasticSearch in the background.


Configuring Elasticsearch and ElasticUtils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can configure ElasticSearch with the configuration file at
``ELASTICDIR/config/elasticsearch.yml``.

There are a series of ``ES_*`` settings in ``fjord/settings/base.py``
that affect ElasticUtils. The defaults will probably work fine. To
override any of the settings, do so in your
``fjord/settings/local.py`` file.

See ``fjord/settings/base.py`` for the list of settings and what they
do.


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


Running the server
==================

To start the dev server, run::

    $ ./manage.py runserver


Then open up the url in your browser.


.. _setting-up-tests:

Running the tests
=================

The test suite will create and use this database, to keep any data in
your development database safe from tests.

Before you run the tests, you have to run these two commands::

    $ ./manage.py collectstatic
    $ ./manage.py compress_assets


Run the test suite this way::

    $ ./manage.py test -s --noinput --logging-clear-handlers


For more information, see the :ref:`test documentation
<tests-chapter>`.


Advanced install
================

After reading the above, you should have everything you need for a
minimal working install which lets you run Fjord and work on many
parts of it.

However, it's missing some things:

* locales: See :ref:`l10n-chapter` for details.


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
