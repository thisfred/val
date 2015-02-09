ACTIVATE = .venv/bin/activate
ACTIVATE2 = .venv2/bin/activate
REQS = pip install -Ur requirements.txt
TESTREQS = pip install -Ur test-requirements.txt
INSTALL = pip install -e '.'

venv: requirements.txt
	test -d .venv || virtualenv -p python3 .venv
	. $(ACTIVATE); $(REQS)
	. $(ACTIVATE); $(TESTREQS)
	. $(ACTIVATE); $(DEVREQS)
	. $(ACTIVATE); $(INSTALL)
	touch $(ACTIVATE)

venv2: requirements.txt
	test -d .venv2 || virtualenv -p python2 .venv2
	. $(ACTIVATE2); $(REQS)
	. $(ACTIVATE2); $(TESTREQS)
	. $(ACTIVATE2); $(DEVREQS)
	. $(ACTIVATE2); $(INSTALL)
	touch $(ACTIVATE2)

vpytest:
	. $(ACTIVATE); py.test -rf -l -s -x  --cov-report term-missing --doctest-glob=*.rst --cov val

vpytest2:
	. $(ACTIVATE2); py.test -rf -l -s -x  --cov-report term-missing --cov val

lint:
	flake8 --max-complexity=10 val tests

test: venv vpytest lint

test2: venv2 vpytest2 lint

clean:
	rm -rf .venv .venv2

pytest: 
	py.test -rf -l -s -x  --cov-report term-missing --cov val

pytest3: 
	py.test -rf -l -s -x  --cov-report term-missing --doctest-glob=*.rst --cov val

travis: pytest lint

