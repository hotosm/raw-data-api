FROM python:3.9-bullseye as python

ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && \
    apt-get -y install gdal-bin python3-gdal && \
    apt-get -y autoremove && \
    apt-get clean

COPY . /app

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -e .

RUN chmod +x Docker/entrypoint.sh

#CMD ["uvicorn", "API.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["Docker/entrypoint.sh"]

HEALTHCHECK CMD curl -f http://localhost:8000 || exit 1
