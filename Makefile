build-binary:
	echo $(VERSION) > ./config/version.txt
	pipenv run pyinstaller opta.spec

lint:
	pipenv run ./scripts/lint.py

test:
	pipenv run pytest .
