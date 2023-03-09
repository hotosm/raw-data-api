#!/usr/bin/env bash

apt-get -y update && \
apt-get -y upgrade && \
apt-get -y install \
  osm2pgsql \
  libpq-dev \
  gdal-bin \
  python3-gdal \
  python-is-python3 \
  python3-virtualenv \
  python3-pip \
  python3-dev \
  redis-tools \
  osmium-tool \
  certbot \
  podman \
  buildah
