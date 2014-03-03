.. _vendor-chapter:

==========================
Maintaining Vendor Library
==========================

To help make setup faster and deployment easier, we pull all of our
pure-Python dependencies into the "vendor library". This chapter talks
about that.


.. contents::
   :local:


vendor
======

The ``vendor/`` directory contains git submodules and unpacked source
for dependencies.

If you cloned Fjord with ``--recursive``, you already have the the
vendor library.

If you didn't clone with ``--recursive``, or you need to update the
submodules, run::

    $ git submodule update --init --recursive


.. Note::

   Aliasing that to something short (e.g. ``gsu``) is recommended.


Updating vendor
===============

From time to time we need to update libraries, either for new versions
of libraries or to add a new library. There are two ways to do
that, but the easiest and prefered way is pure git.


Updating an existing library with git submodules
------------------------------------------------

Using git submodules is prefered because it is much easier to
maintain, and it keeps the repository size small. Upgrading is as
simple as updating a submodule.

If the library is in ``vendor/src``, it was pulled directly from
version control, and if that version control was git, updating the
submodule is as easy as::

    $ cd vendor/src/<LIBRARY-DIR>
    $ git fetch origin
    $ git checkout <REFSPEC>
    $ cd ../..
    $ git add vendor/src/<LIBRARY-DIR>
    $ git ci -m "[bug xyz] Update <LIBRARY>"

Easy peasy!


Adding a new library with git submodules
----------------------------------------

Run::

    $ cd vendor/src
    $ git clone <LIBRARY-REPO>
    $ cd <LIBRARY-DIR>
    $ git checkout <LIBRARY-REPO-REV>
    $ cd ../../..                      # back to fjord project root
    $ vendor/addsubmodules.sh
    $ vim vendor/vendor.pth

    <Add the new library's dir to vendor.pth>

    $ git add vendor/vendor.pth
    $ git ci -m "[bug xyz] Add <LIBRARY>"


Updating a library with pip
---------------------------

The easiest way to update a library with pip is to remove it
completely and then install the new version.

Do::

    $ cd vendor/packages
    $ git rm -r <LIBRARY-DIR>
    $ cd ../..

This puts you in the repository root directory.

After removing the old version, go ahead and install the new one::

    $ pip install --no-install --build=vendor/packages \
        --src=vendor/src -I <LIBRARY>

Finally, add the new library to git::

    $ cd vendor
    $ git add packages
    $ git ci -m "Adding version <VERSION> of <LIBRARY>"


.. Warning::

   **Caveat developer!** Sometimes a library has dependencies that are
   already installed in the vendor repo. You may need to remove
   several of them to make everything work easily.


Adding a library with pip
-------------------------

Adding a new library with pip is easy using pip::

    $ pip install --no-install --build=vendor/packages \
        --src=vendor/src -I <LIBRARY>
    $ cd vendor
    $ git add <LIBRARY>
    $ vim vendor.pth

    <Add the new library's path>

    $ git ci -m "Adding <LIBRARY>"

Make sure you add any dependencies from the new library, as well.

.. Note::

   Need to add a specific version of the library? You can tell pip to install
   a specific version using ``==``. For example::

       $ pip install --no-install --build=vendor/packages \
           --src=vendor/src -I pyes==0.16
