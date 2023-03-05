all:: build test

.PHONY: build
build:
	pip install -r requirements.txt
	python3 -m pip install --upgrade build
	python3 -m build

.PHONY: test
test:
	python -m unittest

.PHONY: lint
lint:
	pycodestyle src/*/*.py test/*.py

.PHONY: install
install:
	pip install dist/bigimageviewer-0.0.1-py3-none-any.whl
