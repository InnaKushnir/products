FROM python:3.10.8

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt mysqlclient

COPY . /code/

RUN  mkdir -p ./data/db

RUN adduser \
    --disabled-password \
    --no-create-home \
    flask-user

RUN chown -R flask-user:flask-user ./data/db
RUN chmod -R 777 ./data/db

USER flask-user