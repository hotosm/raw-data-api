ARG PYTHON_VERSION=3.11

FROM docker.io/python:${PYTHON_VERSION}-slim-bookworm as base

ARG MAINTAINER=sysadmin@hotosm.org
ENV DEBIAN_FRONTEND=noninteractive

FROM base as runner

WORKDIR /home/appuser
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/appuser/.local/bin:$PATH"
ENV PYTHON_LIB="/home/appuser/.local/lib/python$PYTHON_VERSION/site-packages"

# Install runtime dependencies
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get --no-install-recommends -y install libpq5 gdal-bin \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


FROM ghcr.io/hotosm/tippecanoe:main as tippecanoe-builder

FROM runner as with-tippecanoe
COPY --from=tippecanoe-builder /usr/local/bin/tippecanoe* /usr/local/bin/
COPY --from=tippecanoe-builder /usr/local/bin/tile-join /usr/local/bin/

# Builder stage , python dependencies and project setup
FROM base as python-builder

ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get --no-install-recommends -y install \
       build-essential libpq-dev libspatialite-dev libgdal-dev libboost-numpy-dev
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN gdal-config --version | awk -F'[.]' '{print $1"."$2}'

COPY setup.py .
COPY pyproject.toml . 
COPY requirements.txt .
COPY README.md .
COPY LICENSE .

RUN pip install --user --no-cache-dir --upgrade pip setuptools wheel\
    && pip install --user --no-cache-dir GDAL=="$(gdal-config --version)" \
    && pip install --user --no-cache-dir -r requirements.txt
    
RUN python setup.py install --user


<<<<<<< HEAD
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get --no-install-recommends -y install libpq5 gdal-bin \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /home/appuser/.local
COPY README.md .

# Enable this if you are using config.txt
COPY config.txt ./config.txt

COPY setup.py .
COPY pyproject.toml .
COPY API/ ./API/
COPY src/ ./src/
# Use a separate stage to pull the tippecanoe image
FROM ghcr.io/hotosm/tippecanoe:main as tippecanoe-builder

FROM runner as prod

# Copy tippecanoe binaries from the tippecanoe stage
COPY --from=tippecanoe-builder /usr/local/bin/tippecanoe* /usr/local/bin/
COPY --from=tippecanoe-builder /usr/local/bin/tile-join /usr/local/bin/
=======
FROM with-tippecanoe as prod
COPY --from=python-builder /root/.local /home/appuser/.local
>>>>>>> 7235f0f23d099b3b9560917bfd639a244c9def21

RUN useradd --system --uid 900 --home-dir /home/appuser --shell /bin/false appuser \
    && chown -R appuser:appuser /home/appuser

USER appuser

# API and source code, changes here don't invalidate previous layers , You can overwrite this block with -v

# Copy config.txt if you have your configuration setup in config
# COPY config.txt .
COPY README.md .
COPY setup.py .
COPY pyproject.toml .
COPY API/ ./API/
COPY src/ ./src/

CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors", "--proxy-headers"]
