=====================================
Conventions (git, l10n, python, etc.)
=====================================

This document contains coding conventions, and things to watch out
for, etc.


Coding conventions
==================

We follow most of the practices as detailed in the `Mozilla webdev
bootcamp guide
<http://mozweb.readthedocs.org/en/latest/coding.html>`_.

If you don't have an editor that checks PEP-8 issues and runs pyflakes
for you, it's worth setting it up. Use `check.py
<https://github.com/jbalogh/check>`_ because it's awesome.


Git conventions
===============

Git workflow
------------

We use a rebase-based workflow.


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

There should be a blank line between the summary and the rest of the
commit message. Lines shouldn't exceed 72 characters.

See `these guidelines
<http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_
for some more explanation.


Git resources and tools
-----------------------

See `Webdev bootcamp guide
<http://mozweb.readthedocs.org/en/latest/git.html#git-and-github>`_
for:

* helpful resources for learning git
* helpful tools


Localization conventions
========================

Strings
-------

(Copied from Playdoh docs.)

You can localize strings both in python code as well as Jinja templates.

In python::

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

(Copied from Playdoh docs.)

Let’s say you have some template::

    <h1>Hello</h1>

    <p>Is it <a href="http://about.me/lionel.richie">me</a> you're looking for?</p>

Let’s say you are told to translate this. You could do the following::

    {% trans %}
        <h1>Hello</h1>

        <p>Is it <a href="http://about.me/yo">me</a> you're looking for?</p>
    {% endtrans %}

This has a few problems, however:

1. It forces every localizer to mimic your HTML, potentially breaking it.

2. If you decide to change the HTML, you need to either update your
   .po files or buy all your localizers a nice gift because of all the
   pain you’re inflicting upon them.

3.  If the URL changes, your localizer has to update everything.

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
