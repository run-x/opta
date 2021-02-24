build-binary:
	echo $(VERSION) > ./config/version.txt
	pipenv run pyinstaller opta.spec
