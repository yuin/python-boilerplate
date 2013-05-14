[tox]
envlist = py27,py33

[testenv]
deps=PyYAML
     pytest
     pytest-cov

changedir=tests
commands=
  py.test \
    -rxs \
    --cov-report term-missing \
    --cov {{PACKAGE}} \
    --basetemp={envtmpdir}  \ 
    []
