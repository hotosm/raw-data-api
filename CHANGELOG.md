## 1.5.23 (2025-03-29)

### Fix

- **debug**: fixes debug incident

## 1.5.22 (2025-03-29)

### Fix

- **hdx**: adds single category upload after processing is done

## 1.5.21 (2025-03-19)

### Fix

- **sentry**: fixes sentry issue in api workers
- **post_processing**: Update geojson-stats package

## 1.5.20 (2025-03-19)

### Fix

- **post_processing**: Update geojson-stats package for fix missing check for dict prop
- **config**: update SENTRY_DSN to use a placeholder value
- **post_processing**: Fix missing check for property in dict

## 1.5.19 (2025-03-19)

### Fix

- **oldexports**: cleans up old exports based on the env variable

## 1.5.18 (2025-03-04)

### Fix

- **post_processing**: Fixes wrong stats and add more detailed HTML stats for custom exports. Disable transliterations for now

## 1.5.17 (2025-02-18)

### Fix

- **taskreject**: avoid worker acks

## 1.5.16 (2025-02-18)

### Fix

- **workers**: avoid requeue of task if not acks
- **worker**: set task_acks_late to False in api_worker.py

## 1.5.15 (2025-02-11)

### Fix

- **worker**: added worker lost wait in worker
- **worker**: fixes bug on the heartbeat

## 1.5.14 (2025-02-10)

### Fix

- **app.py**: timeout reset

## 1.5.13 (2025-02-03)

### Fix

- **S3FileTransfer.upload**: fix upload when file_path is not a string

## 1.5.12 (2025-01-29)

### Refactor

- Remove unused stats collection, fix stats templates
- Multiple custom visualizations for custom/HDX exports

## 1.5.11 (2025-01-28)

### Fix

- **timeout**: increased timeout for the stats api

## 1.5.10 (2025-01-28)

### Fix

- **stats-endpoint-visualization**: visualization hdx fixes

## 1.5.9 (2025-01-14)

### Fix

- **readonly**: added necessary steps to implement readonly access

## 1.5.8 (2024-12-17)

### Fix

- **hotfixreferrers**: added hot fix to added referrers

## 1.5.7 (2024-12-17)

### Fix

- **folderstats**: fixes folder stats not being populated

## 1.0.16 (2022-12-19)

## 1.0.15 (2022-12-13)

## 1.0.14 (2022-12-13)

## 1.0.13 (2022-12-07)

## 1.0.12 (2022-12-07)

## 1.0.11 (2022-12-07)

## 1.0.10 (2022-12-07)

## 1.0.9 (2022-12-07)

## 1.0.8 (2022-12-07)

## 1.0.7 (2022-12-04)

## 1.5.6 (2024-12-09)

### Fix

- **revert**: reverted changes of post processing for now

## 1.5.5 (2024-12-01)

### Fix

- **hdx-iso-submit**: fixes bug on iso submit for custom exports

### Refactor

- **hdx-cron**: refactors hdx table to cron table

## 1.5.4 (2024-09-12)

### Fix

- **appcustom**: custom exports set srs

## 1.5.3 (2024-09-10)

### Perf

- **mvt**: enhances compatibiltiy of mvt tiles

## 1.5.2 (2024-08-30)

### Fix

- **sytaxbuilder**: fixes syntax on builder append for metadatauser
- **builderbug**: fixes bug on includeuserstats

## 1.5.1 (2024-08-20)

### Fix

- **staff-access-for-download-metrics**: fixes bug for metrics not being available to staff

## 1.5.0 (2024-08-19)

### Feat

- **download-metrics**: enabels user to fetch and download metrics for rawdataapi

## 1.4.6 (2024-08-09)

### Fix

- **unit-test-failing**: only add file format if tiles are enabled

### Perf

- **test-cases**: don't run if task is failed

## 1.4.5 (2024-08-09)

### Fix

- **mvt-tiles**: fixes zoom level and zipping method for mvt tiles

## 1.4.4 (2024-08-09)

### Fix

- **security-patch-task-result**: don't raise the error to user when task status is being returned

## 1.4.3 (2024-08-08)

### Fix

- **mvt-format**: fix bug on mvt formats invalid command line args

## 1.4.2 (2024-08-08)

### Fix

- **fix-zoom-level-bug-on-pmtiles**: adds proper syntax on vector tiles exports zoom level

## 1.4.1 (2024-08-08)

### Fix

- **change-default-db-user-to-user-column**: default user was being used for db query instead read it from table itself
- **fix-on-dir-size-issue**: failing exports causing dir to explode

### Refactor

- **init-default-values**: reinitialize the default value as other endpoints don't require parameters

## 1.4.0 (2024-08-08)

### Feat

- **streaming-response-for-api**: adds streaming response for current snapshot plain
- **userinfo-on-exports**: adds userinfo in exports only for logged in users
- **vector-tiles**: support for vector tiles , allow user to select all tags in select
- **dockerfile**: minimizes docker image size  and introduces new version of gdal which should enable the latest vector driver support
- **custom_exports-yaml**: adds a yaml endpoint for custom exports

### Fix

- **fixes-failing-test-cases**: moves user checking to base class
- **wild-card-select**: fixes bug on wild card select for the query builder

### Refactor

- **cleanup-previous-non-async-code**: removes non async code for the quick fetch
- **yaml-models**: refactor model to models.py
- **custom-exports-yaml**: added geometry and both yaml validation

### Perf

- **custom-exports-yaml**: moves geometry to request body within yaml itself instead of query param

## 1.3.0 (2024-06-06)

### Feat

- **polygon-stats**: let admin and staff bypass the area limit

### Fix

- **iso3-stats**: fix bug on iso3 stats after the role check

## 1.2.2 (2024-05-02)

### Fix

- **api_worker**: clean dir when task fails

## 1.2.1 (2024-04-29)

### Fix

- **hdx-lib**: upgraded the hdx lib to fix last-modified bug

## 1.2.0 (2024-04-05)

### Feat

- **countries**: adds cid country get endpoint

## 1.1.3 (2024-04-05)

### Fix

- **test_api**: unittest fix for plain endpoint

## 1.1.2 (2024-04-04)

### Perf

- **s3downloadlink**: changes download link to support ipv6

## 1.1.1 (2024-03-29)

### Fix

- **stats**: adds area threshold in the stats api along with timeout reduced to 30 second

## 1.1.0 (2024-03-28)

### Feat

- **version-control**: Allows rawdataapi to follow version control using commitizen

### Fix

- **dokcer-compose**: One command up docker compose method
- **dockerfile**: Avoids copying tippicone for source code level changes

### Refactor

- **logging**: adds tqdm for better logging and upgrades hdx python lib
- **queue-name**: changes queue name and workers to pick correct variable
- **api-worker**: logic changes for memory optimized zip

### Perf

- **workers**: enables max worker variable to be set from env variable

## 1.0.17 (2024-03-06)

### Fix

- add optional param to wrap flatgeobuf in geomcollection
- default add spatial index to generated flatgeobuf files

### Refactor

- remove ENCODING param for flatgeobuf (does nothing)
- use f-string for flatgeobuf ogr command

## 1.0.16 (2022-12-19)

## 1.0.15 (2022-12-13)

## 1.0.14 (2022-12-13)

## 1.0.13 (2022-12-07)

## 1.0.12 (2022-12-07)

## 1.0.11 (2022-12-07)

## 1.0.10 (2022-12-07)

## 1.0.9 (2022-12-07)

## 1.0.8 (2022-12-07)

## 1.0.7 (2022-12-04)

## v1.0.6 (2022-09-15)

## v1.0.5 (2022-09-09)

## v1.0.4 (2022-08-02)

## v1.0.3 (2022-08-01)

## v1.0.2 (2022-08-01)

## v1.0.1 (2022-07-29)

## v1.0.0 (2022-07-29)
