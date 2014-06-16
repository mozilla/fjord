.. _workflow-chapter:

======================
 Development workflow
======================

Taking a bug, working on it, sending in changes
===============================================

You found a bug you want to work on! Great! Here's how it works:

1. Comment in the bug that you want to take it. We'll talk with
   you and if it sounds like it's a good fit, we'll assign it to you.

2. Create a new branch. I use the bug number, but it doesn't matter
   what the branch is named. For example::

       git checkout -b 1026503-vagrant-work

3. Work on the changes. Commit your changes to your branch.

4. Go through your changes and make sure they respect our project
   conventions. They're listed in :ref:`conventions-chapter`.

   FIXME - We should add a script that lints PEP-8, jslint, etc
   issues so we don't have to think about those.

5. Send the changes in.

   If you have a GitHub account:

   1. Push your branch to your fork on GitHub.
   2. Create a Pull Request.

   If you don't have a GitHub account:

   1. Use ``git format-patch`` to generate a patch::

          git format-patch --stdout master > bug_<id>.patch 

   2. Attach the patch to the bug.

6. Then we'll talk about the changes and when they're good to land,
   someone with commit permissions will land them.
