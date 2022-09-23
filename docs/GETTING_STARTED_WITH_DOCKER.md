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

Uvicorn should be running on 8000 port , Redis on default port , Celery with a worker and Flower on 5550

```
http://127.0.0.1:8000/latest/docs
```
API Docs will be displayed like this upon uvicorn successfull server start 
![image](https://user-images.githubusercontent.com/36752999/191813795-fdfd46fe-5e6c-4ecf-be9b-f9f351d3d1d7.png)

```
http://127.0.0.1:5550/
```

Flower dashboard will look like this on successfull installation with a worker online 
![image](https://user-images.githubusercontent.com/36752999/191813613-3859522b-ea68-4370-87b2-ebd1d8880d80.png)


Now, Continue Readme. Check installation from [here](../README.md#check-api-installation)
