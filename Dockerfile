FROM python:3.9-bullseye

ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install gdal-bin python3-gdal && \
    apt-get -y autoremove && \
    apt-get clean

RUN mkdir /app
COPY requirements.txt /app/requirements.txt

COPY setup.py /app/setup.py

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

RUN pip install -e .

