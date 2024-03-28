# Raw Data API

![Unit test](https://github.com/hotosm/raw-data-api/actions/workflows/Unit-Test.yml/badge.svg)
![Build](https://github.com/hotosm/raw-data-api/actions/workflows/build.yml/badge.svg)

**Documentation**: [hotosm.github.io/raw-data-api](https://hotosm.github.io/raw-data-api/)

**Source Code**: [github.com/hotosm/raw-data-api](https://github.com/hotosm/raw-data-api)

**API Documentation** : https://api-prod.raw-data.hotosm.org/v1/redoc

`Raw Data API ` is a set of high-performant APIs(Application Programming Interface(s)) for transforming and exporting OpenStreetMap (OSM) data in different GIS file formats.

## Features

- **Fast**: Built on top of [FastAPI](https://fastapi.tiangolo.com/)
- OAUTH 2.0 Authentication with [OpenStreetMap(OSM)](https://openstreetmap.org)
- Multiple GIS formats support via [GDAL's ogr2ogr](https://gdal.org/programs/ogr2ogr.html) - see table below for currently supported formats. Out of which , GeoJSON Follows Own Raw Data API conversion script

  | Formats        | Status             |
  | -------------- | ------------------ |
  | Esri Shapefile | :heavy_check_mark: |
  | KML            | :heavy_check_mark: |
  | Mbtiles        | :heavy_check_mark: |
  | FlatGeoBuf     | :heavy_check_mark: |
  | CSV            | :heavy_check_mark: |
  | GeoPackage     | :heavy_check_mark: |
  | PGDUMP         | :heavy_check_mark: |
  | GeoJSON        | :heavy_check_mark: |
  | Pmtiles        | :heavy_check_mark: |
  | Geoparquet     | :heavy_check_mark: |

## Installation

Raw Data API consists of two elements:

- A **backend** database, tools, and scripts: used to import OSM data into a specific database structure and keep it updated.
- An **API** that is used to serve data from the backend database.

#### To setup the backend see [Backend Installation](./backend/Readme.md)

Raw Data API can be installed through `docker` or locally on your computer.

- To install with docker see [docker installation](./docs/src/installation/docker.md).
- To install locally, see [local installation](./docs/src/installation/local.md).

## Configurations

Setup the necessary configurations for Raw Data API from [configurations](./docs/src/installation/configurations.md).
Setup config.txt in project root or include your env variables in ```.env```

## Basic Usage

- Confirm that Authetication works

  1. Hit the `/auth/login/` endpoint
  2. Hit the `url` returned on the response
  3. You will get an `access_token`
  4. You can use the `access_token` in all endpoints that requires authentication.
  5. To check token pass token in /auth/me/. It should return your OpenStreetMap (OSM) profile

- Try extracting some data:

  You can use the `/raw-data/current-snapshot/` endpoint with the following input to check both authentication, database connection and download the export:

```
curl -d '{"geometry":{"type":"Polygon","coordinates":[[[83.96919250488281,28.194446860487773],[83.99751663208006,28.194446860487773],   [83.99751663208006,28.214869548073377],[83.96919250488281,28.214869548073377],[83.96919250488281,28.194446860487773]]]}}' -H 'Content-Type: application/json'   http://127.0.0.1:8000/v2/raw-data/current-snapshot/
```

## Introduction of sozip

We use [sozip](https://github.com/sozip/sozip-spec) optimization while we zip the files , SOZip makes it possible to access large compressed files directly from a .zip file without prior decompression. It is not a new file format, but a profile of the existing ZIP format, done in a fully backward compatible way. ZIP readers that are non-SOZip aware can read a SOZip-enabled file normally and ignore the extended features that support efficient seek capability. Learn more about it in attached link 


## Tests

- Raw Data API uses pytest for tests, navigate to the root directory and install package in editable mode:

```
pip install -e .
```

- At this point you should have PostgreSQL + PostGIS extension enabled on your computer, now run Pytest:

```
py.test -v -s
```

- Running individual tests

```
py.test -k test function name
```

## Contribution & Development

Learn about current priorities and work going through Roadmap  & see here  [CONTRIBUTING](./docs/src/contributing.md)

## Roadmap
see [Roadmap](https://github.com/orgs/hotosm/projects/29)

## License

see [LICENSE](https://github.com/hotosm/raw-data-api/blob/develop/LICENSE)


## Version Control

For version control, We use commitizen, follow [docs](./docs/src/version_control.md) 

## Authors

Created by [HOTOSM](https://hotosm.org) and [Friends](https://github.com/hotosm/raw-data-api/graphs/contributors)


