.. _es-chapter:

===========================
 Maintaining ElasticSearch
===========================

Things to know about ElasticSearch
==================================

Input uses `ElasticSearch <http://www.elasticsearch.org/>`_ to power
search.

Input uses `ElasticUtils <https://github.com/mozilla/elasticutils>`_
to interface with ElasticSearch.


Command line tools
==================

esreindex: indexing
-------------------

Do a complete reindexing of everything by::

    ./manage.py esreindex

This will delete the existing index specified by ``ES_INDEXES``,
create a new one, and reindex everything in your database.

If you need to get stuff done and don't want to wait for a full
indexing, you can index a percentage of things.

For example, this indexes 10% of your data ordered by id::

    ./manage.py esreindex --percent 10

This indexes 50% of your data ordered by id::

    ./manage.py esreindex --percent 50

I use this when I'm fiddling with mappings and the indexing code.

You can also specify which models to index::

    ./manage.py esreindex --models feedback_simple

See ``--help`` for more details::

    ./manage.py esreindex --help


.. Note::

   If you kick off indexing with the admin, then indexing gets done in
   chunks by celery tasks. If you need to halt indexing, you can purge
   the tasks with::

       ./manage.py celeryctl purge

   If you purge the tasks, you need to cancel outstanding records. Run
   this sql in mysql::

       UPDATE search_record SET status=2 WHERE status=0 or status=1;

   If you do this often, it helps to write a shell script for it.


esstatus: health/statistics
---------------------------

You can see ElasticSearch index status with::

    ./manage.py esstatus

This lists the indexes, tells you which ones are set to read and
write, and tells you how many documents are in the indexes by mapping
type.


esdelete: deleting indexes
--------------------------

You can use the search admin to delete the index.

On the command line, you can do::

    ./manage.py esdelete <index-name>


Live Indexing
=============

When you add data to the database, it needs to be added to the index.
If the setting ``ES_LIVE_INDEX`` is True, then this will be handled
automatically in the ``post_save`` hook as long as celery tasks are
being handled.

For celery tasks to be handled, you have to either have
``CELERY_ALWAYS_EAGER`` set to True, or have at least one celery
worker running, and RabbitMQ working.


Index Maintenance
-----------------

If you don't want live indexing, you can also reindex everything using
the admin or using the esreindex command-line tool, as detailed above.


Debugging tools
===============

See `ElasticUtils documentation <https://elasticutils.readthedocs.io/>`_
for debugging tools and tips.
