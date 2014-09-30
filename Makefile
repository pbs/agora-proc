init:
	pip install -r requirements/requirements.txt

flake:
	flake8 .

pep8:
	autopep8 . --recursive --in-place --pep8-passes 2000 --verbose

clean:
	rm -f agora.tar.gz
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name "*.swp" -print0 | xargs -0 rm -f

tar: clean
	tar -czf agora.tar.gz readme.md setup.py setup.cfg MANIFEST.in requirements/requirements.txt ./agora

test:
	py.test --capture=no

coverage:
	py.test --verbose --cov-report term --cov=agora tests/

ci: init
	py.test --junitxml=junit.xml

generate-fixtures:
	agora -r local --mapper < tests/fixtures/goonhilly-log-sample > tests/fixtures/video-stream-mapper-sample
