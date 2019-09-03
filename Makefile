.PHONY: clean clean-test clean-pyc help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-pyc clean-test clean-coverage ## remove all build, test, coverage and Python artifacts

clean-pyc: ## remove Python file artifacts
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	@find . -name '.pytest_cache' -exec rm -fr {} +

clean-coverage:
	@find . -maxdepth 0 -type f -name ".coverage*" ! -name ".coveragerc"   -exec rm -f {} +
	@rm -fr htmlcov/*

lint: ## check style with flake8
	@flake8
	@bandit --ini .bandit -r

test: clean-coverage ## run tests
	coverage run -m pytest tests/ \
  && coverage report

coverage: test ## check code coverage after tests
	@coverage html
	@$(BROWSER) htmlcov/index.html

install: clean ## install the package to the active Python's site-packages
	@pip install
