# Architecture

## Introduction to the raw-data API

The raw data API consists of two parts:

 - The Backend - composed of LUA and Python scripts that fetch Openstreetmap data in osm.xml format and transform them into geometry that can be stored on PostGIS-compatible PostgreSQL database.
 - The API - the programming interface to the backend that exposes a ReST endpoint to make calls to the database.

## Requirements

- Redis - Acts as a broker and message queue
- Dramatiq - worker management queues

## Deployment Order

1. Backend scripts
2. API service
3. Utility scripts - Deployment not necessary.

## Internal Dependency Graph

              +------------+       +-------+      +-----------+
              |            +------>|       +------>           |
(^_^) -------->  Frontend  |       |  API  <------+  Backend  |
              |            |<------+       |      |           |
Users         +------------+       +--+--^-+      +--+-----^--+
                                      |  |           |     |
                                      |  |           |     |
                                      |  |           |     |
                                      |  |         +-v-----+--+
                                      |  +---------+          |
                                      |            | Database |
                                      +------------>          |
                                                   +----------+

              ┌────────────┐       ┌───────┐      ┌───────────┐
              │            ├──────►│       └──────►           │
(^_^) ────────►  Frontend  │       │  API  ◄──────┐  Backend  │
              │            │◄──────┤       │      │           │
Users         └────────────┘       └──┬──▲─┘      └──┬─────▲──┘
                                      │  │           │     │
                                      │  │           │     │
                                      │  │           │     │
                                      │  │         ┌─▼─────┴──┐
                                      │  └─────────┤          │
                                      │            │ Database │
                                      └────────────►          │
                                                   └──────────┘


## The function of Redis

Redis carries several responsibilities 

 - Act as a task queue
 - Act as a registry for workers (workers are spawned with the knowledge of redis to which they register and from which they pick up jobs - one at a time)


## Architecture diagram

[<img src="../media/arch.png" />](../media/arch.png)
## Export Tool issues

- Export tool still uses Python 2.
- Because Export tool is legacy and fragile, we need to deploy API to a separate VM

