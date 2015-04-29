.. _getting-started-chapter:

=================
 Getting started
=================

.. contents::
   :local:

This guide walks through getting a development environment set up
to allow you to contribute to Fjord.

.. Note::

   This definitely works for Mac OSX and Linux and probably works for
   Windows, too. If you have issues, please let us know.


Getting the requirements
========================

1. Download and install git if you don't have it already:
   http://git-scm.com/

   .. Note::

      **Windows users:** When you install git, make sure to choose
      "Checkout as-is, commit Unix-style line endings". If you don't,
      then you'll end up with Windows-style line endings in your
      checkout and Fjord won't work in the virtual machine.

2. Download and install VirtualBox if you don't have it already:
   https://www.virtualbox.org/

3. Download and install Vagrant if you don't have it already:
   http://www.vagrantup.com/


Download Fjord
==============

If you have a GitHub account, you should fork the Fjord repository and
then clone your fork::

    git clone https://github.com/<USERNAME>/fjord.git

If you do not have a GitHub account, that's ok! Clone the official
Fjord repository this way::

    git clone https://github.com/mozilla/fjord.git

This creates a directory called ``fjord/``. We'll call that the "Fjord
repository top-level directory".

Building a vm and booting it
============================

This will build a VirtualBox vm using Vagrant. The vm will have Ubuntu
Linux 14.04 installed in it. Fjord works in this environment.

Run this commands in the Fjord repository top-level directory::

    vagrant up


It takes a while the first time you do this since it has to create the
virtual machine and provision it. First it downloads an Ubuntu Linux
14.04 image (~300mb), then it installs some software in this image
like MySQL and Elasticsearch. Then it sets things up so that Fjord
runs in this VM using the files on your machine. This allows you to
use whatever editor you like on your machine to edit code that runs in
the VM without having to copy files around.


Setting up Fjord
================

After you've created a vm, we have some minor setup to do::

    # Create a shell on the guest virtual machine
    vagrant ssh

    # Change into the fjord/ directory
    cd ~/fjord


First we download all the product detail data::


    # Update product details
    ./manage.py update_product_details -f


Then we set up the database::

    # Create the database and run migrations
    ./manage.py migrate


Then we create a superuser to log into Fjord::

    ./manage.py createsuperuser


The username and password don't matter, but the email address
does. You must choose an email address that is your Persona
identity. If you don't have a Persona identity, you can create one at
`the Persona site <https://persona.org/>`_.

.. Note::

   You can convert any account into a superuser account by doing::

       ./manage.py ihavepower <email-address>


After that, let's generate some data in the database so that we have
something to look at. We'll then need to index that data so it shows
up in searches.

::

    # Generate sample data
    ./manage.py generatedata

    # Index the sample data into Elasticsearch
    ./manage.py esreindex


That's it!


Editing code and running it
===========================

Fjord is a Django project. We use the Django runserver to run the
website to test it.

First, if you haven't got a running virtual machine, launch it with::

    vagrant up


Then, ssh into the virtual machine::

    vagrant ssh


This gives you a shell in the virtual machine that lets you run all
the Django commands, run the test suite, etc.

To launch the Django runserver, use the vagrant ssh shell and do::

    cd ~/fjord
    ./manage.py runserver 0.0.0.0:8000


Then on your host computer, use your browser and go to
``http://127.0.0.1:8000``. You should see Fjord.


Getting more sample data
========================

Sample data is tied to a specific moment in time. You'll need to run
the generatedata command every time you need fresh data.

The generatedata command only generates data and saves it to the
db. After running generatedata, you'll need to add that data to the
Elasticsearch index::

    ./manage.py generatedata
    ./manage.py esreindex


.. Note::

   You can call generadata as many times as you like.


Virtual machine maintenance commands
====================================

======================  ==================================
Command to run on host  Explanation
======================  ==================================
``vagrant up``          Launches the vm
``vagrant ssh``         SSHs to the vm
``vagrant halt``        Halts the vm
``vagrant status``      Status of the vm
``vagrant destroy``     Destroys the vm (not recoverable!)
======================  ==================================

See more in the `Vagrant documentation
<http://docs.vagrantup.com/v2>`_. If you have questions, let us know.


manage.py commands
==================

You can see the complete list of ``./manage.py`` commands by typing::

    ./manage.py


For each command, you can get help by typing::

    ./manage.py <COMMAND> --help


We use the following ones pretty often:

======================  ====================================================================
Command                 Explanation
======================  ====================================================================
generatedata            Generates fake data so Fjord works
runserver               Runs the Django server
collectstatic           Collects static files and "compiles" them
test                    Runs the unit tests
migrate                 Migrates the db with all the migrations specified in the repository
shell                   Opens a Python REPL in the Django context for debugging
esreindex               Reindexes all the db data into Elasticsearch
esstatus                Shows the status of things in Elasticsearch
update_product_details  Updates the product details with the latest information
ihavepower              Turns a user account into a superuser
======================  ====================================================================


generatedata
------------

You can get sample data in your db by running::

    ./manage.py generatedata


This will generate 5 happy things and 5 sad things so that your Fjord
instance has something to look at.

If you want to generate a lot of random sample data, then do::

    ./manage.py generatedata --with=samplesize=1000


That'll generate 1000 random responses. You can re-run that and also
pass it different amounts. It'll generate random sample data starting
at now and working backwards.


runserver
---------

Vagrant sets up a forward between your host machine and the guest
machine. You need to run the runserver in a way that binds to all the
ip addresses.

Run it like this::

    ./manage.py runserver 0.0.0.0:8000


collectstatic
-------------

When you're running the dev server (i.e. ``./manage.py runserver ...``),
Fjord compiles the LESS files to CSS files and serves them
individually. When you're running Fjord in a server environment, you
run::

    ./manage.py collectstatic

to compile the LESS files to CSS files and then bundle the CSS files
and JS files into single files and minify them. This reduces the
number of HTTP requests the browser has to make to fetch all the
relevant CSS and JS files for a page. It makes our pages load faster.

However, a handful of tests depend on the bundles being built and will
fail unless you run ``collectstatic`` first.


test
----

The test suite will create and use this database, to keep any data in
your development database safe from tests.

Before you run the tests, make sure you run ``collectstatic``::

    ./manage.py collectstatic

I run this any time I run the tests with a clean database.

The test suite is run like this::

    ./manage.py test


For more information about running the tests, writing tests, flags you
can pass, running specific tests and other such things, see the
:ref:`test documentation <tests-chapter>`.


.. _getting-started-chapter-migrate:

migrate
-------

Over time, code changes to Fjord require changes to the
database. We create migrations that change the database from one
version to the next. Whenever there are new migrations, you'll need to
apply them to your database so that your database version is the
version appropriate for the codebase.

To apply database migrations, do this::

    ./manage.py migrate


For more information on the database and migrations, see :ref:`db-chapter`.


shell
-----

This allows you to open up a Python REPL in the context of the Django
project. Do this::

    ./manage.py shell


esreindex and esstatus
----------------------

Fjord uses Elasticsearch to index all the feedback responses in a form
that's focused on search. The front page dashboard and other parts of
the site look at the data in Elasticsearch to do what they do. Thus if
you have no data in Elasticsearch, those parts of the site won't work.

To reindex all the data into Elasticsearch, do::

    ./manage.py esreindex


If you want to see the status of Elasticsearch configuration, indexes,
doctypes, etc, do::

    ./manage.py esstatus


update_product_details
----------------------

Event data like Firefox releases and locale data are all located on a
server far far away. Fjord keeps a copy of the product details local
because it requires this to run.

Periodically you want to update your local copy of the data. You can do that by
running::

    ./manage.py update_product_details


ihavepower
----------

If you create an account on Fjord and want to turn it into a superuser
account that can access the admin, then you need to grant that account
superuser/admin status. To do that, do::

    ./manage.py ihavepower <email-address>


Helpful tips
============

Flushing the cache
------------------

We use memcached for caching. to flush the cache, do::

    echo "flush_all" | nc localhost 11211


Issues with commit timestamps
-----------------------------

The Ubuntu image that we are using, has UTC as the configured timezone.
Due to this, if you are in a different timezone and make commits from
the VM, the commit timestamps will have a different timezone when
compared to the timezone on the host computer. To have matching
timezone on the host and the VM, run::

    sudo dpkg-reconfigure tzdata

and select your current timezone as the timezone for the VM.


Maintaining your development environment
========================================

Fjord is in active development and periodically there are changes that
require you to do something in your development environment.

.. Note::

   Whenever big development environment changes happen, an
   announcement will be sent to the input-dev mailing list. It'll
   usually include instructions on what you should do to update your
   development environment.


Updating your git repository
----------------------------

We land commits to the ``master`` branch of the official repository
regularly. You'll need to update your master branch with the new
commits. You can do that like this::

    $ git checkout master
    $ git pull


Updating your database
----------------------

We periodically change Django models and the changes need to be
reflected in your database tables. To update your database, do this::

    $ ./manage.py migrate

See :ref:`getting-started-chapter-migrate`.


Updating requirements
---------------------

Fjord will often tell you when you need to update your virtualenv
with new requirements. You'll see something like this::

    (fjordvagrant)vagrant@vagrant-ubuntu-trusty-64:~/fjord$ ./manage.py runserver 0.0.0.0:8000
    There are 28 requirements that cannot be checked.
    The following requirements are not satsifed:
    UNSATISFIED: nosenicedots==0.5

    Update your virtual environment by doing:

        ./peep.sh install -r requirements/requirements.txt
        ./peep.sh install -r requirements/compiled.txt
        ./peep.sh install -r requirements/dev.txt

    or run with SKIP_CHECK=1 .


Follow the instructions to update them.


Where to go from here?
======================

:ref:`conventions-chapter` covers project conventions for Python,
JavaScript, git usage, etc.

:ref:`workflow-chapter` covers the general workflow for taking a bug,
working on it and submitting your changes.

:ref:`db-chapter` covers database-related things like updating your
database with new migrations, creating migrations, etc.

:ref:`es-chapter` covers Elasticsearch-related things like maintaining
your Elasticsearch index, reindexing, getting status, deleting the
index and debugging tools.

:ref:`l10n-chapter` covers how we do localization in Fjord like links
to the svn repository where .po files are stored, Verbatim links,
getting localized strings, updating strings in Verbatim with new
strings, testing strings with Dennis, linting strings, creating new
locales, etc.

:ref:`tests-chapter` covers testing in Fjord like running the tests,
various arguments you can pass to the test runner to make debugging
easier, running specific tests, writing tests, the smoketest system,
JavaScript tests, etc.

:ref:`vendor-chapter` covers maintaining ``vendor/`` and the Python
library dependencies in there.
