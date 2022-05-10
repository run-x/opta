FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED=1

COPY requirements.txt  ./requirements.txt

RUN pip install -r requirements.txt

RUN mkdir /app

WORKDIR /app

RUN mkdir static

COPY . /app

RUN chmod +x startup.sh

CMD ["bash", "startup.sh" ]