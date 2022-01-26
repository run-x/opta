set -e
set -x

export PYTHONPATH=$(pwd)

source $(pipenv --venv)/bin/activate

gunicorn --bind 0.0.0.0:5000 wsgi:app
