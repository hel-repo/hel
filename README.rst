Hel Package Repository
======================
A package database and repository of OpenComputers & ComputerCraft programs.

Build Status
------------
Master branch: |travis-ci-master|

Dev branch: |travis-ci-dev|

.. |travis-ci-master| image:: https://travis-ci.org/hel-repo/hel.svg?branch=master
   :alt: Travis CI build status
   :target: https://travis-ci.org/hel-repo/hel

.. |travis-ci-dev| image:: https://travis-ci.org/hel-repo/hel.svg?branch=dev
   :alt: Travis CI build status
   :target: https://travis-ci.org/hel-repo/hel

Getting Started - Usage
-----------------------
Just open this link in your favorite browser:
https://hel-roottree.rhcloud.com/

Getting Started - Dev
---------------------
- Install python>=3.3, MongoDB 3.2
- Clone Hel git repository to local directory
- ``$ export VENV=<full path to directory containing hel project>/env``
- ``$ pip3 install virtualenv``
- ``$ python3 -m virtualenv $VENV``
- ``$ cd <directory containing this file>``
- ``$ $VENV/bin/pip install -e .``
- ``$ $VENV/bin/pserve development.ini``

This will set up and run a local copy of hel.
http://127.0.0.1:6543/

Testing
-------
To be able to run tests you need to install additional packages with the following command:

``$ $VENV/bin/pip install -e '.[testing]'``

And there's the command to actually run tests:

``$ $VENV/bin/py.test``

By default, it also performs "PEP8 sanity checks", and stops after fifth failture.
