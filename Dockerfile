# Base image with GDAL and Python
ARG GDAL_VERSION=3.9.0
FROM ghcr.io/osgeo/gdal:ubuntu-small-$GDAL_VERSION as base

ARG MAINTAINER=sysadmin@hotosm.org

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip python3-venv build-essential libpq-dev python3-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /home/appuser
ENV PATH="/home/appuser/venv/bin:$PATH"

RUN python3 -m venv /home/appuser/venv && \
    /home/appuser/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml uv.lock /home/appuser/
RUN /home/appuser/venv/bin/pip install --no-cache-dir uv && \
    /home/appuser/venv/bin/uv pip sync --python /home/appuser/venv/bin/python

COPY README.md /home/appuser/
COPY API/ /home/appuser/API/
COPY src/ /home/appuser/src/
COPY alembic/ /home/appuser/alembic/
COPY alembic.ini /home/appuser/

RUN /home/appuser/venv/bin/pip install --no-cache-dir .

FROM ghcr.io/osgeo/gdal:ubuntu-small-$GDAL_VERSION

WORKDIR /home/appuser
RUN useradd --system --uid 900 --home-dir /home/appuser --shell /bin/false appuser && \
    chown -R appuser:appuser /home/appuser

ENV PATH="/home/appuser/venv/bin:$PATH"
COPY --from=base /home/appuser /home/appuser

USER appuser

CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors", "--proxy-headers"]
