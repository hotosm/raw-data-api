# Base image with GDAL and Python 3.12+
ARG GDAL_VERSION=3.12.0
ARG PYTHON_VERSION=3.12
FROM ghcr.io/osgeo/gdal:ubuntu-small-$GDAL_VERSION AS base

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

COPY pyproject.toml uv.lock LICENSE README.md /home/appuser/
COPY src/ /home/appuser/src/
RUN /home/appuser/venv/bin/pip install --no-cache-dir uv && \
    /home/appuser/venv/bin/uv sync --frozen

COPY API/ /home/appuser/API/
COPY alembic/ /home/appuser/alembic/
COPY alembic.ini /home/appuser/

RUN /home/appuser/venv/bin/pip install --no-cache-dir .

FROM ghcr.io/osgeo/gdal:ubuntu-small-$GDAL_VERSION AS final

WORKDIR /home/appuser
RUN useradd --system --uid 900 --home-dir /home/appuser --shell /bin/false appuser && \
    chown -R appuser:appuser /home/appuser

ENV PATH="/home/appuser/venv/bin:$PATH"
COPY --from=base /home/appuser /home/appuser

USER appuser

CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors", "--proxy-headers"]
