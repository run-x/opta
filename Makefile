build-binary:
	echo $(VERSION) > ./config/version.txt
	pyinstaller --paths $(shell pipenv --venv) --add-data ./config:config --name opta --onefile opta/cli.py
