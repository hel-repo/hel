Hel Package Repository
======================
A package database and repository of OpenComputers & ComputerCraft programs.

Getting Started - Usage
-----------------------
Just open this link in your favorite browser:
http://hel-roottree.rhcloud.com/

Getting Started - Dev
---------------------
- Install python>=3.3, MongoDB 3.2
- Clone Hel git repository to local directory
- ``$ export VENV=<full path to directory containing hel project>/env``
- ``$ python3 -m venv $VENV``
- ``$ cd <directory containing this file>``
- ``$ $VENV/bin/pip install -e .``
- ``$ $VENV/bin/pserve development.ini``

This will setup and run local copy of hel.
http://127.0.0.1:6543/

Testing
-------
To be able to run tests you need to install additional packages with the following command:

``$ $VENV/bin/pip install -e '.[testing]'``

And there's the command to actually run tests:

``$ $VENV/bin/py.test``

By default, it also performs "PEP8 sanity checks", and stops on first failture.
