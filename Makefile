all:
	python3 -m pip install --upgrade build
	python3 -m build

install:
	pip install dist/bigimageviewer-0.0.1-py3-none-any.whl
