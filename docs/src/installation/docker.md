## Initial Setup

- Clone the repository, and change directory to _export-tool-api_ folder on your computer.

```
git clone https://github.com/hotosm/export-tool-api.git
cd export-tool-api
```

## Configurations

- Create `config.txt` inside / folder. You can use any of the appropriate commands below or you use your familiar methods in your code editor/file explorer.

```
touch config.txt #Linux
wsl touch config.txt #Windows with WSL
echo >> config.txt #Windows without WSL
```

- Database configuration:
  - To use the default database(with sample data) shipped with the `Dockerfile`, you can update the `config.txt` with the configurations below. [**Recommended**]
  - To use a local postgres (with postgis enabled) database, you can follow the instruction on how to set it up with raw data [here](./configurations.md). or export them as system env variables

```
[DB]
PGHOST=pgsql
PGUSER=postgres
PGPASSWORD=admin
PGDATABASE=raw
PGPORT=5432

[API_CONFIG]
RATE_LIMITER_STORAGE_URI=redis://redis:6379

[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

- OSM Authentication:

  - Follow this step to setup OSM OAuth: [Setup Oauth Block](./configurations.md#Setup-Oauth-for-Authentication).
  - Update your `config.txt` with the `[OAUTH]` block from the step above.

## Create the Docker images and spin up the containers

```
docker-compose up -d --build
```

## Check the servers

By default, Uvicorn would be running on port [8000](http://127.0.0.1:8000/v1/docs), Redis on default port(i.e 6379), Celery with a worker and Flower on port [5000](http://127.0.0.1:5000/).

- API Documentation

Visit the route below to access the API documentation.

```
http://127.0.0.1:8000/v1/docs
```

API docs will be displayed like this upon successfull server startup

![image](https://user-images.githubusercontent.com/13560473/204081940-e680a0d3-dcb4-43ff-ad09-5886671ffaff.png)

- Flower dashboard

Vist the route below to access the Flower dashboard

```
http://127.0.0.1:5000/
```

Flower [dashboard](http://127.0.0.1:5000/) will look like this on successfull installation with a worker online.

![image](https://user-images.githubusercontent.com/36752999/191813613-3859522b-ea68-4370-87b2-ebd1d8880d80.png)

## Proceed to the readme for further configurations: [here](../index.md#Installation).

## **Troubleshooting**

**NOTE:** If any of the solutions provided below does not work for you, please don't hesistate to open an issue.

- If you can't connect to your local postgres database from `export-tool-api`.

  Since _export-tool-api_ is running in docker containers, it means if you setup your `config.txt` file to use a local postgres database on your machine, the database port may not be accessible as `localhost` from the docker containers. To solve this, docker needs to connect to your local network. Try any of these hacks to troubleshoot the issue:

  1. Option one :

     - For windows/ Mac docker user
       Replace localhost with `host.docker.internal` – This resolves to the outside host and lets you connect to your machine's localhost through container. For example if postgres is running on your machine on port `5432` , docker container can connect from `host.docker.internal:5432`
     - For linux user :
       Linux users can enable host.docker.internal via the --add-host flag for docker run. Start your containers with this flag to expose the host string:
       `docker run -d --add-host host.docker.internal:host-gateway my-container:latest`

  2. Option two :

     - Find your network ip address (for linux/mac you can use `ifconfig -l | xargs -n1 ipconfig getifaddr` ) and use your ip address as the database host instead of `localhost` in `config.txt` file.
     - If connection still fails : You may need to edit your postgres config file ( ask postgres where it is using this query: `show config_file;` ) and edit/enable `listen_addresses = '*'` inside `postgresql.conf` . Also add `host all all 0.0.0.0/0 trust` in `pg_hba.conf`.
