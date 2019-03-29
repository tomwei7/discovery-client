check:
	python setup.py check
test:
	python -m unittest discover tests

.PHONY: check test
