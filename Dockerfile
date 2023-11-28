ARG PYTHON_VERSION=3.10

FROM docker.io/python:${PYTHON_VERSION}-slim-bookworm as base

ARG MAINTAINER=sysadmin@hotosm.org
ENV DEBIAN_FRONTEND=noninteractive

FROM base as builder

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
COPY requirements.txt .
COPY README.md .
RUN pip install --user --no-cache-dir --upgrade pip \
    && pip install --user --no-cache-dir GDAL=="$(gdal-config --version)" \
    && pip install --user --no-cache-dir -r requirements.txt \
    && pip install --user --no-cache-dir -e .

FROM base as runner
WORKDIR /home/appuser
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/appuser/.local/bin:$PATH"
ENV PYTHON_LIB="/home/appuser/.local/lib/python$PYTHON_VERSION/site-packages"

RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get --no-install-recommends -y install libpq5 gdal-bin \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /home/appuser/.local
COPY README.md .
COPY config.txt.sample ./config.txt
COPY setup.py .
COPY API/ ./API/
COPY src/ ./src/
# Use a separate stage to pull the tippecanoe image
FROM ghcr.io/hotosm/tippecanoe:main as tippecanoe-builder

FROM runner as prod

# Copy tippecanoe binaries from the tippecanoe stage
COPY --from=tippecanoe-builder /usr/local/bin/tippecanoe* /usr/local/bin/
COPY --from=tippecanoe-builder /usr/local/bin/tile-join /usr/local/bin/

RUN useradd --system --uid 900 --home-dir /home/appuser --shell /bin/false appuser \
    && chown -R appuser:appuser /home/appuser

USER appuser

# CMD ["/bin/bash"]
CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors", "--proxy-headers"]