build-binary:
	pyinstaller --paths $(shell pipenv --venv) --add-data ./config:config --name opta  opta/cli.py
