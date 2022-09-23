FROM python:3.9-bullseye

ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install gdal-bin python3-gdal && \
    apt-get -y autoremove && \
    apt-get clean

COPY . /app

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.docker.txt
RUN pip install -e .

COPY /src/config.txt src/config.txt

HEALTHCHECK CMD curl -f http://localhost:8000/latest/docs || exit 1
