# Base image with GDAL and Python
ARG GDAL_VERSION=3.9.0
FROM ghcr.io/osgeo/gdal:ubuntu-small-$GDAL_VERSION as base

ARG MAINTAINER=sysadmin@hotosm.org

# Install libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip python3-venv build-essential libpq-dev python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /home/appuser
ENV PATH="/home/appuser/venv/bin:$PATH"

RUN python3 -m venv /home/appuser/venv && \
    /home/appuser/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt requirements.lock
RUN /home/appuser/venv/bin/pip install --no-cache-dir -r requirements.lock


# Copy application files
COPY osm2pgsql-query-builder/ /home/appuser/osm2pgsql-query-builder/
COPY README.md setup.py pyproject.toml /home/appuser/
COPY API/ /home/appuser/API/
COPY src/ /home/appuser/src/

RUN /home/appuser/venv/bin/pip install --no-cache-dir ./osm2pgsql-query-builder && \
    /home/appuser/venv/bin/pip install --no-cache-dir .

# Final image
FROM ghcr.io/osgeo/gdal:ubuntu-small-$GDAL_VERSION

WORKDIR /home/appuser
RUN useradd --system --uid 900 --home-dir /home/appuser --shell /bin/false appuser && \
    chown -R appuser:appuser /home/appuser

ENV PATH="/home/appuser/venv/bin:$PATH"
COPY --from=base /home/appuser /home/appuser

USER appuser

CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors", "--proxy-headers"]
