include README.rst
include setup.py
include tox.ini

recursive-include {{PACKAGE}} *
recursive-include tests *

global-exclude __pycache__
global-exclude .coverage
global-exclude  *.py[co]
global-exclude  *.db
global-exclude  .git*
