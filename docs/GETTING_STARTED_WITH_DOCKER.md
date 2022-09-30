### 1. First Checkout the repository  and Setup Config

```
git clone https://github.com/hotosm/galaxy-api.git
```

Follow [instructions](../docs/CONFIG_DOC.md) and create config.txt inside /src/


### 2. Create the images and spin up the Docker containers:
```
docker-compose up -d --build
```

### 3. Check Servers

Uvicorn should be running on 8000 port , Redis on default port , Celery with a worker and Flower on 5000

```
http://127.0.0.1:8000/latest/docs
```
API Docs will be displayed like this upon uvicorn successfull server start
![image](https://user-images.githubusercontent.com/36752999/191813795-fdfd46fe-5e6c-4ecf-be9b-f9f351d3d1d7.png)

```
http://127.0.0.1:5000/
```

Flower dashboard will look like this on successfull installation with a worker online
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
