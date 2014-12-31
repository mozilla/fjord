.. _db-chapter:

====================
 Maintaining the db
====================

Updating the db
===============

If someone pushes changes that change the db, you'll need to apply the
new migrations to your db. Do this::

    ./manage.py syncdb
    ./manage.py migrate


Creating a schema migration
===========================

We use `South <http://south.aeracode.org/>`_ for database migrations.

To create a new migration the automatic way:

1. make your model changes
2. run::

       ./manage.py schemamigration <app> --auto


   where ``<app>`` is the app name (base, feedback, analytics, ...).

3. run the migration on your machine::

       ./manage.py migrate

4. run the tests to make sure everything works
5. add the new migration files to git
6. commit


.. seealso::

   http://south.readthedocs.org/en/latest/tutorial/index.html
     South tutorial


Creating a data migration
=========================

Creating data migrations is pretty straight-forward in most cases.

To create a data migration the automatic way:

1. run::

       ./manage.py datamigration <app> <name>

   where ``<app>`` is the app name (base, feedback, analytics, ...) and
   ``<name>`` is the name of the migration

2. edit the data migration you just created to do what you need it to
   do
3. add the new migration file to git
4. commit

.. seealso::

   http://south.readthedocs.org/en/latest/tutorial/part3.html#data-migrations
     South tutorial: data migrations


Backwards migrations
--------------------

Make sure to write backwards code if you can. If there's no way to undo
the migration, then do this::

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")


Data migrations for data in non-Fjord apps
------------------------------------------

If you're doing a data migration that adds data to an app that's not
part of Fjord, but is instead a library (e.g. django-waffle), then
create the data migration in the base app and make sure to freeze the
library app so that it's available.

For example, this creates a waffle flag::

    ./manage.py datamigration base create_gengo_switch --freeze waffle
