### 1. First Checkout the repository  and Setup Config

```
git clone https://github.com/hotosm/galaxy-api.git
```

Follow [instructions](https://github.com/hotosm/galaxy-api/blob/develop/docs/CONFIG_DOC.md) and create config.txt inside /src/

### 2. Create the images and spin up the Docker containers:
```
docker-compose up -d --build
```

### 3. Check Servers

Uvicorn should be running on 8000 port , Redis on default port , Celery with a worker and Flower on 5550

```
http://127.0.0.1:8000/latest/docs
```
```
http://127.0.0.1:8000/5550/
```

Now follow Readme.md
