build-binary:
	echo $(VERSION) > ./config/version.txt
	pipenv run pyinstaller opta.spec

lint:
	pipenv run ./scripts/lint.py --apply

test:
	pipenv run pytest .

security_tests:
	pipenv run bandit -r ./opta