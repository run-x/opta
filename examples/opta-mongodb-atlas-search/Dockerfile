FROM python:3.9-slim
# TODO python version needs to be templatized
WORKDIR /home/app
RUN pip install pipenv

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy

COPY . /home/app

CMD ["bash", "startup.sh" ]
