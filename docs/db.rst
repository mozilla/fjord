====================
 Maintaining the db
====================

Setting up and configuring the db
=================================

See :ref:`hacking-howto-db` for setting up the database tables, users,
and permissions.

See :ref:`hacking-howto-configuration` for setting configuration
settings for accessing the database.

See :ref:`hacking-howto-schemas` for initializing the tables in the db.


Updating the db
===============

If someone pushes changes that change the db, you need to update your
db. Do this::

    $ ./manage.py syncdb
    $ ./manage.py migrate


Creating a schema migration
===========================

We use `South <http://south.aeracode.org/>`_ for database migrations.

To create a new migration the automatic way:

1. make your model changes
2. run::

       $ ./manage.py schemamigration <app> --auto


   where ``<app>`` is the app name (base, feedback, analytics, ...).

3. run the migration on your machine::

       $ ./manage.py migrate

4. run the tests to make sure everything works
5. add the new migration files to git
6. commit


.. seealso::

   http://south.readthedocs.org/en/latest/tutorial/index.html
     South tutorial


Creating a data migration
=========================

.. seealso::

   http://south.readthedocs.org/en/latest/tutorial/part3.html#data-migrations
     South tutorial: data migrations
