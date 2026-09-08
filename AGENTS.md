<!-- markdownlint-disable MD013 MD025 -->

# AGENTS.md

Guidance for AI coding agents in **raw-data-api**.
Human maintainers are accountable for all merged changes.

---

## Project

Raw Data API serves OpenStreetMap data extracts in GIS formats, on demand and
on a schedule. It is the export backend behind the Export Tool, HDX exports,
and other HOT services, so its API surface and output formats are consumed by
downstream systems.

**Stack:** Python 3.11 / FastAPI / PostgreSQL + PostGIS (osm2pgsql schema) /
Celery-style async workers (`API/api_worker.py`) / GDAL / S3 / pytest

---

## Required Reading Order

1. `README.md` - features, configuration, and how to run tests.
2. `backend/Readme.md` and `backend/Manual.md` - how the OSM database backend
   is built and replicated. Read these before touching any SQL or Lua.
3. `docs/src/contributing.md` - contribution rules, including AI tool usage.
4. `docs/src/installation/` - the installation path you are working against.

---

## Structure

```text
API/                  # FastAPI routers: raw_data, tasks, auth, s3, stats,
                      # custom_exports, cron, metrics, download_metrics
API/api_worker.py     # async export worker
src/app.py            # core export logic
src/query_builder/    # SQL generation for OSM extracts
src/post_processing/  # output conversion and packaging
src/validation/       # request models and validation
src/config.py         # configuration loading (config.txt / env)
backend/              # osm2pgsql Lua styles, SQL, replication, country data
tests/                # pytest suite
docs/src/             # MkDocs documentation
infra/                # Terraform and deployment infrastructure
```

---

## Commands

```bash
pip install -e .            # install in editable mode (needs GDAL: gdal-bin, python3-gdal)
py.test -v -s               # full test suite (needs PostgreSQL + PostGIS)
py.test -k <test_name>      # a single test
```

Docker install path: see `docs/src/installation/docker.md`. Database backend
setup: see `backend/Readme.md`.

Formatting is enforced in CI by `black` and `isort` (isort uses the `black`
profile). Run both before opening a PR - there is a dedicated
`black-for-PR` workflow that will fail otherwise.

---

## Decisions Already Made

- **The database schema comes from osm2pgsql with HOT's Lua styles**
  (`backend/raw.lua`, `backend/raw_with_ref.lua`). Query generation targets
  that schema. Do not introduce an ORM or a second schema.
- **SQL generation lives in `src/query_builder/`.** Keep query construction
  there rather than inlining SQL into routers.
- **Exports run in a worker, not in request handlers.** An API call queues a
  task and returns a task id; clients poll `tasks`.
- **Routers are feature-flagged.** Several routers (`custom_exports`, `stats`,
  `metrics`, `cron`, `s3`) are only mounted when their feature is enabled in
  config - preserve that behaviour when adding endpoints.
- **The API surface is consumed by other HOT services.** A response-shape
  change is a breaking change; version it and flag it explicitly.

Approaches previously tried and rejected are not recorded in-repo. Ask a
maintainer rather than assuming a design is accidental.

---

## Where AI Help Is Welcome

- Tests for existing behaviour
- Documentation and docstrings
- Validation models and error handling
- Tightly scoped bug fixes with a reproducing test

## Where AI Must Not Act Unsupervised

- Generated SQL and the Lua styles (`src/query_builder/`, `backend/*.lua`,
  `backend/sql/`) - a wrong query here can be extremely expensive to run
- Authentication (`API/auth/`) and any rate limiting
- S3 access and credential handling (`API/s3.py`)
- Replication (`backend/replication/`)
- `infra/` (Terraform) and the deploy workflows
- Anything that changes an existing response shape

---

## Coding Standards

- Format with `black`; sort imports with `isort` (`profile = "black"`, and keep
  the configured import section headings).
- Parameterise every query. String-interpolating user input into SQL is
  forbidden - `src/query_builder/` is the only place SQL is assembled.
- Geospatial correctness matters: be explicit about CRS and do not assume
  polygons are well-behaved.
- Long-running work belongs in the worker, never in a request handler.

---

## Testing Standards

- New behaviour needs a test in `tests/`.
- Tests require a local PostgreSQL + PostGIS and GDAL; say so if you could not
  run them rather than reporting a pass you did not see.
- Never weaken or skip a failing test to make a change pass.

---

## Anti-Patterns

- Inline SQL in routers
- Committing secrets; `config.txt.sample` is the reference
- Version bumps by hand - versioning is managed by `bumpver`
- Broad reformat-the-world diffs mixed into a behavioural change
- Adding a heavyweight dependency where GDAL or the existing stack suffices

---

## Workflow

1. Read the relevant router, the query builder, and the tests before changing
   code.
2. Keep the diff scoped to the task; raise anything else separately.
3. Run `py.test -v -s` (or the narrowest relevant selection) plus `black` and
   `isort`.
4. Report what you changed, what you ran, and what you did not verify.

When uncertain, ask instead of assuming.

---

## Responsible AI Contribution Policy

- Org guidance for AI-assisted contributions: <https://responsibleai.guide>
- Declare the AI assistance level (0-5) in the PR template honestly. Never
  lower the declared level to get a PR reviewed.
- If nobody has read the result, that is level 5: open the PR as a draft.
- Do not work on issues labelled `good first issue` - they exist for humans.
- A human is accountable for every merged change.
