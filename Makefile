build-binary:
	echo $(VERSION) > ./config/version.txt
	pipenv run pyinstaller --paths $(shell pipenv --venv) --add-data ./config:config --name opta opta/cli.py
