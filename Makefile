JANSKY_ENV ?= "jansky.env"
DC := $(shell which docker-compose)

default:
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "build         - build docker containers for dev"
	@echo "run           - docker-compose up the entire system for dev"
	@echo ""
	@echo "shell         - open a shell in the base container"
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "lint          - check style with flake8"
	@echo "test          - run tests"
	@echo "test-coverage - run tests and generate coverage report in cover/"
	@echo "docs          - generate Sphinx HTML documentation, including API docs"

# Dev configuration steps
.docker-build:
	make build

build:
	JANSKY_ENV=empty.env ${DC} build deploy-base
	JANSKY_ENV=empty.env ${DC} build dev-base
	touch .docker-build

run: .docker-build
	JANSKY_ENV=${JANSKY_ENV} ${DC} up jansky

shell: .docker-build
	JANSKY_ENV=empty.env ${DC} run --service-ports base bash

clean:
	# python related things
	-rm -rf build/
	-rm -rf dist/
	-rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

	# test related things
	-rm -f .coverage
	JANSKY_ENV=empty.env ${DC} run base rm -rf cover

	# docs files
	-rm -rf docs/_build/

	# state files
	-rm .docker-build
	-rm -rf fakes3_root/

lint: .docker-build
	JANSKY_ENV=empty.env ${DC} run base flake8 --statistics jansky tests/unittest/
	JANSKY_ENV=empty.env ${DC} run base bandit -r jansky/

test: .docker-build
	JANSKY_ENV=empty.env ${DC} run base py.test

test-coverage: .docker-build
	JANSKY_ENV=empty.env ${DC} run base py.test --cov=jansky --cov-report term-missing

docs: .docker-build
	JANSKY_ENV=empty.env ${DC} run base ./bin/build_docs.sh

.PHONY: default help clean build docs lint run shell test test-coverage
