ARG GDAL_VERSION=3.8.4
FROM ghcr.io/osgeo/gdal:ubuntu-small-${GDAL_VERSION} as build

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    gcc \
    make \
    libpq-dev \
    && python3 -m pip install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/appuser

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

FROM ghcr.io/osgeo/gdal:ubuntu-small-${GDAL_VERSION} as final

WORKDIR /home/appuser

COPY --from=build /usr/local /usr/local

RUN rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

COPY --chown=appuser:appuser . .

CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors", "--proxy-headers"]
