test-all: tox lint
test: pytest lint

pytest:
	py.test -rf -l -s -x  --cov-report term-missing --cov val
tox:
	tox
lint:
	flake8 --max-complexity=10 val tests
