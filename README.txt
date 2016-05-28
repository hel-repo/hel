Hel Package Repository
======================
Package repository and database, for OpenComputers & ComputerCraft programs.

Getting Started - Usage
-----------------------
Just open this link in your favorite browser:
http://hel-roottree.rhcloud.com/

Getting Started - Dev
---------------------
- Install python>=3.3, MongoDB 3.2
- Clone Hel git repository to local directory
- $ export VENV=<full path to directory containing hel project>/env
- $ python3 -m venv $VENV
- $ cd <directory containing this file>
- $ $VENV/bin/pip install -e .
- $ $VENV/bin/pserve development.ini

This will setup and run local copy of hel.
http://127.0.0.1:6543/
