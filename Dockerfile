FROM python:3.9-bullseye

ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install gdal-bin python3-gdal && \
    apt-get -y autoremove && \
    apt-get clean

RUN mkdir /app
COPY requirements.docker.txt /app/requirements.docker.txt
COPY populate-docker-db.sh /docker-entrypoint-initdb.d/
COPY docker-multiple-db.sh /docker-entrypoint-initdb.d/
COPY /tests/src/fixtures/insights.sql /insights.sql
COPY /tests/src/fixtures/mapathon_summary.sql /mapathon_summary.sql
COPY /tests/src/fixtures/raw_data.sql /raw_data.sql
COPY /tests/src/fixtures/underpass.sql /underpass.sql
COPY /tests/src/fixtures/tasking-manager.sql /tasking-manager.sql


COPY setup.py /app/setup.py

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.docker.txt

COPY . /app

RUN pip install -e .

HEALTHCHECK CMD curl -f http://localhost:8000/latest/docs || exit 1
