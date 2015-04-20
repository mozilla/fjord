.. _conventions-chapter:

=============================================
Project Conventions (git, l10n, Python, etc.)
=============================================

.. contents::
   :local:

This document contains coding conventions, and things to watch out
for, etc.


Coding conventions
==================

Editor configuration
--------------------

We use .editorconfig to codify and enforce editor settings using
editorconfig (http://editorconfig.org/). Install the editorconfig
plugin for your editor to make use of the recommended settings.


Git pre-commit hook
-------------------

We have a Git pre-commit hook that makes it easier to make sure you're
checking in linted code. To set it up, run::

    $ ./bin/hooks/lint.pre-commit

That'll set up the pre-commit hook. After that, every time you commit
something in Git, it'll run the hook first and if everything is fine
continue with the commit. If things are not fine, it'll notify you and
stop.


Python conventions
------------------

Follow `PEP-8 <http://python.org/dev/peps/pep-0008/>`_ for code and
`PEP-257 <http://python.org/dev/peps/pep-0257/>`_ for docstrings.

If you don't have an editor that checks PEP-8 issues and runs pyflakes
for you, it's worth setting it up.

You can also use the linting script ``bin/flake8_lint.sh``::

    $ ./bin/flake8_lint.sh <files-to-lint>


JavaScript
----------

Use `jshint <http://www.jshint.com/>`_ for JavaScript code. This is
automatically done in the pre-commit hook.

Use `jsdoc <http://usejsdoc.org/>`_ for JavaScript function documentation.


Git conventions
===============

Git commit messages
-------------------

Git commit messages should have the following form::

    [bug xxxxxxx] Short summary

    Longer explanation with paragraphs and lists and all that where
    each line is under 72 characters.

    * bullet 1
    * bullet 2

    Etc. etc.


Summary line should be capitalized, short and shouldn't exceed 50
characters. Why? Because this is a convention many git tools take
advantage of.

If the commit relates to a bug, the bug should show up in the summary
line in brackets.

Lines shouldn't exceed 72 characters.

See `these guidelines
<http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_
for some more explanation.


Localization conventions
========================

Strings
-------

You can localize strings both in Python code as well as Jinja
templates.

In Python::

    from tower import ugettext as _, ugettext_lazy as _lazy

    yodawg = _lazy('The Internet')

    def myview(request):
        return render('template.html', {msg=_('Hello World'), msg2=yodawg})

``_lazy`` is used when we are not in scope of a request. This lets us
evaluate a string, such as yodawg, at the last possible second when we
finally can draw upon the request’s context. E.g. in a template::

    {{ msg2 }}

Will be evaluated to whatever The Internet is in the requester’s
locale.

In Jinja we can use the following syntax for localized strings::

    <h1>{{ _('Hello') }}</h1>

    {% trans link='http://mozilla.org' %}
      <p>Go to this <a href="{{ link }}">site</a>.</p>
    {% endtrans %}


Good Practices
--------------

Let’s say you have some template::

    <h1>Hello</h1>

    <p>
      Is it <a href="http://about.me/lionel.richie">me</a> you're
      looking for?
    </p>

Let’s say you are told to translate this. You could do the following::

    {% trans %}
      <h1>Hello</h1>

      <p>
        Is it <a href="http://about.me/yo">me</a> you're looking for?
      </p>
    {% endtrans %}

This has a few problems, however:

1. It forces every localizer to mimic your HTML, potentially breaking
   it.

2. If you decide to change the HTML, you need to either update your
   .po files or buy all your localizers a nice gift because of all the
   pain you’re inflicting upon them.

3. If the URL changes, your localizer has to update everything.

Here’s an alternative::

    <h1>_('Hello')</h1>

    <p>
      {% trans about_url='http://about.me/lionel.richie' %}
        Is it <a href="{{ about_url }}">me</a> you're looking for?
      {% endtrans %}
    </p>

or if you have multiple paragraphs::

    <h1>_('Hello')</h1>

    {% trans about_url='http://about.me/lionel.richie' %}
      <p>
        Is it <a href="{{ about_url }}">me</a> you're looking for?
      </p>
      <p>
        I can see it in your eyes.
      </p>
    {% endtrans %}

Here are the advantages:

1. Localizers have to do minimal HTML.
2. The links and even structure of the document can change, but the
   localizations can stay put.

Be mindful of work that localizers will have to do.


.. seealso::

   http://playdoh.readthedocs.org/en/latest/userguide/l10n.html#localization-l10n
     Localization (l10n) in the Playdoh docs


Testing strings
---------------

Fjord comes with ``bin/test_locales.sh`` script which makes it pretty
easy to test that strings in the user interface are getting gettext'd.
It creates a faux "Pirate" translation of the strings in the `xx` locale.

You need to install polib for the script to work::

    $ pip install polib

After that, cd into the project directory and do::

    $ bin/test_locales.sh

After that runs, you can see what happened by doing::

    $ ./manage.py runserver 0.0.0.0:8000

and going to `<http://127.0.0.1:8000/xx/>`_.
