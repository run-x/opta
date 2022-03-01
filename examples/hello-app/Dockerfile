FROM python:3.10-slim-buster

ENV FLASK_APP=app

WORKDIR /app

RUN pip install Flask==2.0
COPY . /app
ENV PORT 80

CMD python3 -m flask run --host=0.0.0.0 --port=${PORT}
