NOTE: The installation guide below is only tested to work on Ubuntu, we recommend using docker for other operating systems.

### Local Installation Requirements.

- Install [GDAL](https://gdal.org/index.html) on your computer using the command below:

```
sudo apt-get update && \
sudo apt-get -y install gdal-bin python3-gdal && \
sudo apt-get -y autoremove && \
sudo apt-get clean

```

- Install [redis](https://redis.io/docs/getting-started/installation/) on your computer using the command below:

```
sudo apt-get -y install redis
sudo apt-get -y install redis-tools # For client
```

- Confirm Redis Installation

```
redis-cli
```

Type `ping` it should return `pong`.

If _redis_ is not running check out its [documentation](https://redis.io/docs/getting-started/)

- Clone the Raw Data API repository on your computer

```
git clone https://github.com/hotosm/raw-data-api.git
```

- Navigate to the repository directory

```
cd raw-data-api
```

- Install the python dependencies

```
pip install -r requirements.txt
```

### Optional : For Tiles Output
If you opt for tiles output and have ```ENABLE_TILES : True``` in env variable . Make sure you install [Tippecanoe] (https://github.com/felt/tippecanoe)

### Set up your database
- Ensure postgres is installed and running :
``` bash
  sudo apt-get install postgresql postgresql-contrib
  service postgresql start 
  service postgresql status
```

- Install postgis
```bash
  sudo apt-get install postgis
``` 

- Create a database
```bash
  su postgres
  psql
  > CREATE DATABASE db_name;
  > \q
```

- Setup postgis on that database
```bash
  su postgres
  psql -U postgres db_name
  > CREATE EXTENSION  postgis;
  > \q
```

### Prevent eventlet epoll error

To prevent
```
AttributeError: module 'eventlet.green.select' has no attribute 'epoll'
```
Set EVENTLET_NO_GREENDNS to "yes"
```bash
  export EVENTLET_NO_GREENDNS=yes
```

### Create your configuration file

Follow instructions from [configurations.md](./configurations.md).

### Start the Server

```
uvicorn API.main:app --reload
```

### Queues 

Currently there are two type of queue implemented : 
- "raw_daemon" : Queue for default exports which will create each unique id for exports  , This queue is attached to 24/7 available workers 
- "raw_ondemand" : Queue for recurring exports which will replace the previous exports if present on the system , can be enabled through uuid:false API Param . This queue will be attached to worker which will only spin up upon request. 

### Start Celery Worker

You should be able to start [celery](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#running-the-celery-worker-server) worker by running following command on different shell

- Start for default daemon queue 
  ```
  celery --app API.api_worker worker --loglevel=INFO --queues="raw_daemon" -n 'default_worker'
  ```
- Start for on demand queue 
  ```
  celery --app API.api_worker worker --loglevel=INFO --queues="raw_ondemand" -n 'ondemand_worker'
  ```

Set no of request that a worker can take at a time by using --concurrency 

#### Note
`If you are using postgres database as result_backend for celery you need to install sqlalchemy`
```bash
pip install SQLAlchemy==2.0.25
```
### Start flower for monitoring queue [OPTIONAL]

Raw Data API uses flower for monitoring the Celery distributed queue. Run this command on a different shell , if you are running redis on same machine your broker could be `redis://localhost:6379//`.

```
celery --broker=redis://redis:6379// --app API.api_worker flower --port=5000 --queues="raw_daemon,raw_ondemand"
```

OR Simply use flower from application itself

```bash
celery --broker=redis://localhost:6379// flower
```

### Navigate to the docs to view Raw Data API endpoints

After sucessfully starting the server, visit [http://127.0.0.1:8000/v1/docs](http://127.0.0.1:8000/v1/docs) on your browser to view the API docs.

```
http://127.0.0.1:8000/v1/docs
```

Flower dashboard should be available on port `5000` on your localhost.

```
http://127.0.0.1:5000/
```
