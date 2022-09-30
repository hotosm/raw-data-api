### 1. First Checkout the repository  and Setup Config

```
git clone https://github.com/hotosm/galaxy-api.git
```

- Create config.txt inside /src/

```
touch src/config.txt
```

- Put those config block inside your file

If you want to use docker postgres Sample data for underpass, insights, taskingmanager, rawdata is included in db itself :
You can use following config to get started with sample data  or Setup them by yourself by following [instructions](../docs/CONFIG_DOC.md)
```
[INSIGHTS]
host=pgsql
user=postgres
password=admin
database=insights
port=5432

[UNDERPASS]
host=pgsql
user=postgres
password=admin
database=underpass
port=5432

[TM]
host=pgsql
user=postgres
password=admin
database=tm
port=5432

[RAW_DATA]
host=pgsql
user=postgres
password=admin
database=raw
port=5432

[API_CONFIG]
env=dev

[CELERY]
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

- **Setup Authentication**

   Follow this [Setup Oauth Block](../docs/CONFIG_DOC.md#6-setup-oauth-for-authentication) and include it in your config.txt

### 2. Create the images and spin up the Docker containers:
```
docker-compose up -d --build
```

### 3. Check Servers

Uvicorn should be running on [8000](http://127.0.0.1:8000/latest/docs) port , Redis on default port , Celery with a worker and Flower on 4000

```
http://127.0.0.1:8000/latest/docs
```
API Docs will be displayed like this upon uvicorn successfull server start
![image](https://user-images.githubusercontent.com/36752999/191813795-fdfd46fe-5e6c-4ecf-be9b-f9f351d3d1d7.png)

```
http://127.0.0.1:4000/
```

Flower [dashboard](http://127.0.0.1:4000/) will look like this on successfull installation with a worker online
![image](https://user-images.githubusercontent.com/36752999/191813613-3859522b-ea68-4370-87b2-ebd1d8880d80.png)


Now, Continue Readme. Check installation from [here](../README.md#check-api-installation)

### [Troubleshoot] If you can't connect to local postgres from API

Since API is running through container, If you have local postgres installed on your machine that port may not be accesible as localhost from container , Container needs to connect to your local network , In order to do that there are few options
1. Option one :

   - For windows/ Mac docker user
     Replace localhost with ```host.docker.internal``` – This resolves to the outside host and lets you connect to your machine's localhost through container , For example if postgres is running on your machine in 5432 , container can connect from ```host.docker.internal:5432```
   - For linux user :
     Linux users can enable host.docker.internal too via the --add-host flag for docker run. Start your containers with this flag to expose the host string:
     ```docker run -d --add-host host.docker.internal:host-gateway my-container:latest```

2. Option two :

    Find your network ip address (for linux/mac you can use ```ifconfig -l | xargs -n1 ipconfig getifaddr``` ) and use your ip as a host instead of localhost in config file .

    If connection still fails : You may need to edit your postgres config file ( ask postgres where it is by this query ```show config_file;``` ) and edit/enable ```listen_addresses = '*'``` inside ```postgresql.conf``` . Also add ```host    all             all             0.0.0.0/0               trust``` in ```pg_hba.conf```

### [Troubleshoot] If you can't run postgresql on docker to execute .sh script provided

Make your .sh script executable . For eg : In ubuntu/mac

```
chmod +x populate-docker-db.sh && chmod +x docker-multiple-db.sh
```
