.. _es-chapter:

===========================
 Maintaining ElasticSearch
===========================

Things to know about ElasticSearch
==================================

Input uses `ElasticSearch <http://www.elasticsearch.org/>`_ to power
search.

Input uses the `ElasticUtils
<https://github.com/mozilla/elasticutils>`_ library to interface with
ElasticSearch.


Installing ElasticSearch
========================

There's an installation guide on the ElasticSearch site.

http://www.elasticsearch.org/guide/reference/setup/installation.html

We're currently using 0.17.x in production.

The directory you install Elastic in will hereafter be referred to as
``ELASTICDIR``.


Running ElasticSearch
=====================

Start Elastic Search by::

    $ ELASTICDIR/bin/elasticsearch

That launches Elastic Search in the background.


Configuring ElasticUtils
========================

You can configure ElasticSearch with the configuration file at
``ELASTICDIR/config/elasticsearch.yml``.

There are a series of ``ES_*`` settings in ``fjord/settings/base.py``
that affect ElasticUtils. The defaults will probably work fine. To
override any of the settings, do so in your
``fjord/settings/local.py`` file.

See ``fjord/settings/base.py`` for the list of settings and what they
do.

.. Note::

   If you're running Input in a vm, you'll want to set
   ``ES_TEST_SLEEP_DURATION``. This causes the test harness to sleep a
   bit between indexing things and querying the index.  This gives
   ElasticSearch a chance to catch up.

   For example, this sets it to 1 second::

       ES_TEST_SLEEP_DURATION = 1


Command line tools
==================

esreindex: indexing
-------------------

Do a complete reindexing of everything by::

    $ ./manage.py esreindex

This will delete the existing index specified by ``ES_INDEXES``,
create a new one, and reindex everything in your database.

If you need to get stuff done and don't want to wait for a full
indexing, you can index a percentage of things.

For example, this indexes 10% of your data ordered by id::

    $ ./manage.py esreindex --percent 10

This indexes 50% of your data ordered by id::

    $ ./manage.py esreindex --percent 50

I use this when I'm fiddling with mappings and the indexing code.

You can also specify which models to index::

    $ ./manage.py esreindex --models feedback_simple

See ``--help`` for more details::

    $ ./manage.py esreindex --help


.. Note::

   Once you've indexed everything, if you have ``ES_LIVE_INDEXING``
   set to ``True``, you won't have to do it again unless indexing code
   changes. The models have ``post_save`` and ``pre_delete`` hooks
   that will update the index as the data changes.


.. Note::

   If you kick off indexing with the admin, then indexing gets done in
   chunks by celery tasks. If you need to halt indexing, you can purge
   the tasks with::

       $ ./manage.py celeryctl purge

   If you purge the tasks, you need to reset the Redis scoreboard.
   Connect to the appropriate Redis and set the value for the magic
   key to 0. For example, my Redis is running at port 6383, so I::

       $ redis-cli -p 6383 set search:outstanding_index_chunks 0

   If you do this often, it helps to write a shell script for it.


esstatus: health/statistics
---------------------------

You can see Elastic Search index status with::

    $ ./manage.py esstatus

This lists the indexes, tells you which ones are set to read and
write, and tells you how many documents are in the indexes by mapping
type.


esdelete: deleting indexes
--------------------------

You can use the search admin to delete the index.

On the command line, you can do::

    $ ./manage.py esdelete <index-name>


Maintaining your index
======================

When you add data to the database, it needs to be added to the index.
This happens automatically in the post_save hook as long as celery
tasks are being handled.

You can also reindex everything using the admin or using the esreindex
command-line tool.


Debugging tools
===============

See `ElasticUtils documentation
<http://elasticutils.readthedocs.org/en/latest/index.html>`_ for
debugging tools and tips.
