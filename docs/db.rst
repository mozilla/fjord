.. _db-chapter:

====================
 Maintaining the db
====================

Updating the db
===============

If someone pushes changes that change the db, you'll need to apply the
new migrations to your db. Do this::

    ./manage.py migrate


Creating a schema migration
===========================

To create a new migration the automatic way:

1. make your model changes
2. run::

       ./manage.py makemigrations <app>


   where ``<app>`` is the app name (base, feedback, analytics, ...).

3. add a module-level docstring to the new migration file specifying
   what it's doing since we can't easily infer that from the code
   because the code shows the new state and not the differences
   between the old state and the new stage

4. run the migration on your machine::

       ./manage.py migrate

5. run the tests to make sure everything works
6. add the new migration files to git
7. commit


.. seealso::

   https://docs.djangoproject.com/en/1.7/topics/migrations/#adding-migrations-to-apps
     Django documentation: Adding migrations to apps


Creating a data migration
=========================

Creating data migrations is pretty straight-forward in most cases.

To create a data migration the automatic way:

1. run::

       ./manage.py makemigrations --empty <app>

   where ``<app>`` is the app name (base, feedback, analytics, ...)

2. edit the data migration you just created to do what you need it to
   do
3. make sure to add `reverse_code` arguments to all `RunPython` operations
   which undoes the changes
4. add a module-level docstring explaining what this migration is doing
5. run the migration forwards and backwards to make sure it works
   correctly
6. add the new migration file to git
7. commit

.. seealso::

   https://docs.djangoproject.com/en/1.7/topics/migrations/#data-migrations
     Django documentation: Data Migrations

.. seealso::

   https://docs.djangoproject.com/en/1.7/ref/migration-operations/#runpython


Data migrations for data in non-Fjord apps
------------------------------------------

If you're doing a data migration that adds data to an app that's not
part of Fjord, but is instead a library (e.g. django-waffle), then
create the data migration in the base app and add a dependency to
the latest migration in the library app.

For example, this adds a dependency to django-waffle's initial migration::

    class Migration(migrations.Migration):

        dependencies = [
            ...
            ('waffle', '0001_initial'),
            ...
        ]
