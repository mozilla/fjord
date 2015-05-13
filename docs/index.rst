=================================
Welcome to Fjord's documentation!
=================================

.. _overview:

Overview
========

Fjord is the software that runs `Mozilla Input
<https://input.mozilla.org/>`_. The site has two sides to it: one for
gathering product feedback and user sentiment and the other for
exposing that data and analytics on it. The Mozilla Input feedback
site helps us understand what 450 million users are thinking and makes
it possible for us to catch issues we wouldn't otherwise be able to
know about.

This is at heart a `Django <http://djangoproject.com>`_-powered
site. It uses a `MySQL <http://mysql.com>`_ database for data storage
and an `Elasticsearch <http://elasticsearch.org>`_ cluster for search,
analytics and facets.


Project details:

:wiki:         https://wiki.mozilla.org/Firefox/Input
:code:         https://github.com/mozilla/fjord
:new bugs:     https://bugzilla.mozilla.org/enter_bug.cgi?product=Input&rep_platform=all&op_sys=all
:irc:          #input on irc.mozilla.org
:mailing list: https://mail.mozilla.org/listinfo/input-dev
:get involved: https://wiki.mozilla.org/Webdev/GetInvolved/input.mozilla.org


.. yippie:: Yay!

   
Contents
========

Want to contribute to Input? Then this is the section for you! Start
with :ref:`contributors-chapter` which will guide you through the rest.

.. toctree::
   :maxdepth: 2

   welcome
   getting_started
   workflow
   conventions
   testing
   db
   es
   l10n
   vendor


Part 2: Using the Site
======================

Are you an Input user? This is the section for you!

.. toctree::
   :maxdepth: 1

   feedback_urls
   api
   hb_api
   alerts_api
   events_api


Part 3: Maintaining The Site
============================

Are you one of those super sekret gnomes that maintain the site
through wintry blizzards and fiery summers? This is the section for
you!

.. toctree::
   :maxdepth: 1

   maintain
   sla
