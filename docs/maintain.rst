=============================
 Maintaining Fjord and Input
=============================

.. contents::
   :local:


Onboarding a new developer
==========================

1. Watch the "Input" product and "__Any__" component in Bugzilla in your
   `Bugzilla Component Watching preferences
   <https://bugzilla.mozilla.org/userprefs.cgi?tab=component_watch>`_

2. Hop on the ``#input`` IRC channel on irc.mozilla.org

3. Create an IT bug for getting added to error email lists

4. Ask an existing developer with an admin account on Input to create an
   admin account for you

5. Get access to push changes to ``https://github.com/mozilla/fjord``

6. Update the `wiki page <https://wiki.mozilla.org/Firefox/Input>`_

7. Read the documentation:

   :manual: http://fjord.rtfd.org/
   :wiki page: https://wiki.mozilla.org/Firefox/Input

8. Set up your development environment by reading through and doing all
   the things in the :ref:`hacking-howto-chapter`

9. If you haven't read through the `Webdev Bootcamp
   <http://mozweb.readthedocs.org/en/latest/>`_, now is a good time

10. Bask in the tranquil rhythmic sounds of the Fjord


Adding support for a new product
================================

To add support for a new product via product urls for the feedback form or the
Input API, add a new entry to the Products table.


Adding a new locale
===================

To add a new locale so that ``https://input.mozilla.org/%NEWLOCALE%`` works
and so that people can see the site in that language and submit feedback:

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


Making strings changes to feedback forms
========================================

Feedback forms must be fully translated in specific target locales *before*
they can be pushed to production.

Process for making feedback form strings changes:

1. create a new branch

2. make the changes you need to make

3. submit a pull request

4. after the pull request is approved (r+), extract and merge strings
   from that branch

5. send an email to the dev-l10n-web mailing list---see :ref:`l10n-update-strings`
   for details


Now you have to wait until the target locales have fully translated the new
strings.

Use the ``bin/l10n_status.py`` script to tell you whether things are good
to go or not.

Once they're good to go, you can land the changes in master and push to
stage and production.

For the list of target locales per form, see Cheng, Matt or Will.


Dealing with errors in translated strings
=========================================

When we deploy a new version of Fjord, it updates the ``.po`` files and
picks up newly translated strings.

``.po`` files that have errors will not get compiled to ``.mo`` files
and thus won't go to production and thus won't cause fires.

Note that this doesn't mean that this locale will have no
translations---we'll use the previously compiled ``.mo`` file.

If there is no ``.mo`` file, then the deployment will compile
a ``.mo`` file even if there are errors with the figuring that
a problematic ``.mo`` file is better than nothing and that this
should be an exceedingly rare occurrence.

If ``.po`` files have errors, then those errors are noted in the
postatus.txt files:

* dev: https://input-dev.allizom.org/media/postatus.txt
* stage: https://input.allizom.org/media/postatus.txt
* prod: https://input.mozilla.org/media/postatus.txt

If there are errors in those files, we need to open up a bug in
**Mozilla Localizations** -> *locale code* with the specifics.

Bug description template::

    We found errors in the translated strings for Input (https://input.mozilla.org/).
    The errors are as follows:


    <paste errors here>


    Until these errors are fixed, we can't deploy updates to the strings for this locale.

    If you have any questions, let me know.
