## Initial Setup

### Clone 

- Clone the repository, and change directory to _raw-data-api_ folder on your computer.

```
git clone https://github.com/hotosm/raw-data-api.git
cd raw-data-api
```

## Configurations

### config.txt approach
- Create `config.txt` inside / folder. You can use any of the appropriate commands below or you use your familiar methods in your code editor/file explorer. (if you are using `docker-compose` , you can edit `docker-compose-config.txt`)

```
touch config.txt #Linux
wsl touch config.txt #Windows with WSL
echo >> config.txt #Windows without WSL
```
#### .env approach 

if you prefer configurations as env variables you can put them in `.env` and pass it to dockerfile or export them 

- Database configuration:
  - To use the default database(with sample data) , Run docker compsoe and  update the `docker-compose-config.txt` 

  - To use a local postgres (with postgis enabled) database, you can follow the instruction on how to set it up with raw data [here](./configurations.md). or export them as system env variables


- OSM Authentication:

  - Follow this step to setup OSM OAuth: [Setup Oauth Block](./configurations.md#Setup-Oauth-for-Authentication).
  - Update your `config.txt` with the `[OAUTH]` block from the step above.


## Run Docker 

You can either use full composed docker-compose directly or you can build docker containers manually . 

### Spin up the containers using docker compose

```
docker-compose up -d --build
```

### Setting Environment Variables in Docker Container

To configure the environment variables `PYTHONPATH` and `ACCESS_TOKEN` in your Docker container, follow the steps below:

#### PYTHONPATH

- The `PYTHONPATH` environment variable specifies the directories where Python looks for modules and packages.
- In the context of your Docker container, setting `PYTHONPATH` to the present working directory (`pwd`) means that Python will search for modules and packages in the current directory.
- This is particularly useful when you have custom modules or packages in your project that you want Python to recognize and import.

#### ACCESS_TOKEN

- `ACCESS_TOKEN` is an environment variable used for authentication purposes.
- To obtain the `ACCESS_TOKEN`, you need to generate a login URL for authentication using an OAuth2 application registered with OpenStreetMap.
- Click on the generated URL, which will redirect you to the OpenStreetMap authentication page.
- After logging in and authorizing the OAuth2 application, OpenStreetMap will provide an `ACCESS_TOKEN`.
- Set the obtained `ACCESS_TOKEN` as an environment variable in the Docker container.
- This allows your application to use the token for making authenticated requests to OpenStreetMap APIs.

In summary, configuring the `PYTHONPATH` to the present working directory enables Python to find modules and packages in your project, while obtaining the `ACCESS_TOKEN` involves generating a login URL for OAuth2 authentication with OpenStreetMap and setting the resulting token as an environment variable in the Docker container for authentication purposes.

OR 

### Run Docker without docker compose for development

- Build your image 
```
docker build -t rawdataapi:latest . 
```
- Run API 
```
docker run --name rawdataapi -p 8000:8000 \
    -v "$(pwd)/API:/home/appuser/API" \
    -v "$(pwd)/src:/home/appuser/src" \
    -v "$(pwd)/config.txt:/home/appuser/config.txt" \
    rawdataapi:latest \
    uvicorn API.main:app --reload --host "0.0.0.0" --port "8000" --no-use-colors --proxy-headers
```

- Run Workers 
```
docker run --name rawdata-worker \
    -v "$(pwd)/API:/home/appuser/API" \
    -v "$(pwd)/src:/home/appuser/src" \
    -v "$(pwd)/config.txt:/home/appuser/config.txt" \
    rawdataapi:latest \
    celery --app API.api_worker worker --loglevel=INFO --queues="raw_ondemand" -n 'default_worker'
```
- Run Flower on port 5555
```
docker run --name rawdata-flower -p 5555:5555 \
    -v "$(pwd)/API:/home/appuser/API" \
    -v "$(pwd)/src:/home/appuser/src" \
    -v "$(pwd)/config.txt:/home/appuser/config.txt" \
    rawdataapi:latest \
    celery --broker=redis://redis:6379// --app API.api_worker flower --port=5555 --queues="raw_daemon,raw_ondemand"
```

**Development instruction:** 
If you are running Dockerfile only for the API , Have postgresql redis installed on your machine directly then you should change following : 

- Change --broker Host address in flower command (You can use redis if it is docker compsoe container or use `redis://host.docker.internal:6379/0` if you want API container to connect to your localhsot , Follow #troubleshoot section for more)
- Change DB Host & Celery broker url accordingly with the same logic 


**Note:**

In above example we have attached our working dir to containers along with config.txt for efficiency in development environment only . It is recommended to use proper docker copy as stated in dockerfile and system environement variables instead of config.txt in Production

## Check the servers

By default, Uvicorn would be running on port [8000](http://127.0.0.1:8000/v1/docs), Redis on default port(i.e 6379), Celery with a worker and Flower on port [5555](http://127.0.0.1:5555/).

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
http://127.0.0.1:5555/
```

Flower [dashboard](http://127.0.0.1:5555/) will look like this on successfull installation with a worker online. (Change the port accordingly to your command)

![image](https://user-images.githubusercontent.com/36752999/191813613-3859522b-ea68-4370-87b2-ebd1d8880d80.png)

## Proceed to the readme for further configurations: [here](../index.md#Installation).

## **Troubleshooting**

**NOTE:** If any of the solutions provided below does not work for you, please don't hesistate to open an issue.

- If you can't connect to your local postgres database from `raw-data-api`.

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
