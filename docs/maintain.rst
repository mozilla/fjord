=============================
 Maintaining Fjord and Input
=============================

Adding a new locale
===================

To add a new locale so that ``https://input.mozilla.org/%NEWLOCALE%`` works
and so that people can submit feedback:

1. In your local repository, run::

       $ ./manage.py update_product_details

2. Check ``lib/product_details_json/languages.json`` to see if the language is
   there.

   1. If not, you need to file a bug to get it added. See
      https://bugzilla.mozilla.org/show_bug.cgi?id=839506 for example.

   Once the locale is listed in
   ``lib/product_details_json/languages.json``, proceed.

3. Update ``locale/`` and check to see if the locale is listed there.

   1. If you don't have a ``locale/`` directory or don't know how to update it,
      see :ref:`l10n-chapter`.
   2. If the locale isn't in the ``locale/`` directory, ask Milos to
      add Input to the list of translated projects for that
      locale. See https://bugzilla.mozilla.org/show_bug.cgi?id=860754
      for better language because I only vaguely understand how the
      Verbatim side works.

   Once the locale is in svn and ``locale/``, proceed.

4. Add the locale code to the ``PROD_LANGUAGES`` list in
   ``fjord/settings/base.py``.

5. Commit the changes to ``fjord/settings/base.py`` and product details stuff
   to git.


.. Note::

   To test this in a local instance, you need to have::

       DEV_LANGUAGES = PROD_LANGUAGES

   in your ``fjord/settings/local.py``. Otherwise ``DEV_LANGUAGES`` is
   the list of locales in ``locales/``.

   After making that change, you can go to
   ``https://127.0.0.1:8000/%NEWLOCALE%`` and it won't redirect to
   ``https://127.0.0.1:8000/en-US/%NEWLOCALE%``.


.. Note::

   https://input-dev.allizom.org/ uses ``DEV_LANGUAGES``, so any changes
   you make to ``PROD_LANGUAGES`` won't affect the -dev environment.

   You'll have to do the testing on the staging environment.
