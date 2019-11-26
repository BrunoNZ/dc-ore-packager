.PHONY: updatetools install build clean uploadtest upload

PY=python3

updatetools:
	python3 -m pip install --user --upgrade setuptools wheel twine

install:
	$(PY) setup.py install --user

build:
	$(PY) setup.py sdist bdist_wheel

clean:
	$(PY) setup.py clean --all
	@rm -rf ./dc_ore_packager.egg-info
	@rm -rf ./dist

uploadtest: updatetools clean build
	$(PY) -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload: updatetools clean build
	$(PY) -m twine upload dist/*
