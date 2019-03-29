check:
	python setup.py check
test:
	python -m unittest discover tests

package:
	python setup.py sdist
	python setup.py bdist_wheel

.PHONY: check test package
