build-binary:
	pyinstaller --paths $(shell pipenv --venv) --add-data ./opta/registry.yaml:opta --add-data ./opta/debugger.yaml:opta --name opta --onefile opta/cli.py
