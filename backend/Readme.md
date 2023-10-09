## Getting Started

- Install [osm2pgsql > v1.6.0](https://osm2pgsql.org/doc/install.html)

  ```
  sudo apt-get install osm2pgsql
  ```

- Install other system dependencies that are necessary to build the system

  ```
  sudo apt -y install python-is-python3 # for sanity
  sudo apt -y install python3-virtualenv
  sudo apt -y install libpq-dev # for building psycopg2
  ```

- Clone rawdata and navigate to backend dir

  ```
  git clone https://github.com/hotosm/raw-data-api.git && cd backend
  ```

- Install Requirements

  Install [psycopg2](https://pypi.org/project/psycopg2/), [osmium](https://pypi.org/project/osmium/) and [dateutil](https://pypi.org/project/python-dateutil/) , wget in your python env . You can install using `requirements.txt` too

  ```
  pip install -r requirements.txt
  ```

  - Start the Process

  You can either export your db params as env variables or pass to script , or create .env and hit `source .env`

  ```
  export PGHOST=localhost
  export PGPORT=5432
  export PGUSER=admin
  export PGPASSWORD=admin
  export PGDATABASE=postgres
  ```

  Choose your source for the Import

  > You can Download Planet pbf file [Here](https://planet.osm.org/pbf/) or Use Geofabrik Pbf file [Here](https://osm-internal.download.geofabrik.de/index.html) with full metadata (Tested with .pbf file) , or pass download link to script itself . Follow -h help

  - Test with the sample data

    ```
    python raw_backend --insert
    ```

    > This will insert the sample data provided on the code , You can check your backend setup with this

  - For eg : To import Turkey and Enable replication later on

    ```
    python raw_backend --insert --replication --source https://download.geofabrik.de/europe/turkey-latest.osm.pbf --country 127
    ```

    > Here Insert option will do the import after downloading osm.pbf file from source , You can supply filepath of already downloaded file to --source as well . Replication will enable and Prepare the tables for replication and start the replication right away until data becomes now , Country parameter is read from fid of /backend/countries which will make sure to only maintains the replication data for that country

  
  - Import your osm file and run replication for only your custom geojson 

    ```
      python raw_backend --replication --boundary pokhara.geojson
    ```
    Example of geojson : 
      ```
          {
          "type": "Feature",
          "properties": {},
          "geometry": {
            "coordinates": [
              [
                [
                  83.90895770965955,
                  28.279633888511327
                ],
                [
                  83.90895770965955,
                  28.131383546395526
                ],
                [
                  84.10168708213502,
                  28.131383546395526
                ],
                [
                  84.10168708213502,
                  28.279633888511327
                ],
                [
                  83.90895770965955,
                  28.279633888511327
                ]
              ]
            ],
            "type": "Polygon"
          }
        }
      ```


  To Run Replication only

  ```
  python raw_backend --replication
  ```

  > By default this command will run replciation until data becomes up to date and exit ! You can run this script on your custom frequency by specifying your cron / prefeered way to wake the script do the job and sleep



  Options to Run the Script :

  ```
  -h, --help            show this help message and exit
  --source SOURCE       Data source link or file path
  --host HOST           DB host
  --port PORT           DB port
  --user USER           DB user
  --password PASSWORD   DB password
  --database DATABASE   DB name
  --include_ref         Include ref in output tables
  --replication         Prepare tables for replication and Runs Replication
  --country COUNTRY     id of the country , if you are loading country , it will filter replication data
  --boundary            Takes geojson file path or geojson string itself to keep replication within the region
  --insert              Run osm2pgsql to insert data , Initial Creation Step
  --update              Run Update on table fields for country info
  --download_dir DOWNLOAD_DIR
                          The directory to download the source file to
  --post_index          Run Post index only on table
  ```

  If you are interested on Manual setup find Guide [here](./Manual.md)

## Running the backend service via Systemd

- Create a systemd unit file for raw-data-backend service

```
$ sudo systemctl edit --full --force raw-data-backend.service
```

```
[Unit]
Description=Raw Data Backend Service
Documentation=https://github.com/hotosm/raw-data-api/blob/develop/backend/Readme.md
After=network.target syslog.target
Wants=network-online.target systemd-networkd-wait-online.service
StartLimitIntervalSec=500
StartLimitBurst=5

[Service]
Type=simple
User=hotsysadmin
WorkingDirectory=/opt/raw-data-api/backend
ExecStart=/opt/raw-data-api/backend/venv/bin/python raw_backend --replication
Restart=on-failure
EnvironmentFile=/opt/raw-data-api/backend/PGCRED.env
Type=simple
Restart=on-failure
RestartSec=5s
WatchdogSec=43200

[Install]
WantedBy=multi-user.target
```
- Start Your service and look at the status
```
$ sudo systemctl start raw-data-backend.service
$ sudo systemctl status raw-data-backend.service
```

```
● raw-data-backend.service - Raw Data Backend Service
     Loaded: loaded (/etc/systemd/system/raw-data-backend.service; disabled; vendor preset: enabled)
     Active: active (running) since Mon 2023-02-13 14:30:03 UTC; 4min 25s ago
       Docs: https://github.com/hotosm/raw-data-api/blob/develop/backend/Readme.md
   Main PID: 50561 (python)
      Tasks: 9 (limit: 4700)
     Memory: 94.7M
        CPU: 14.996s
     CGroup: /system.slice/raw-data-backend.service
             ├─50561 /opt/raw-data-api/backend/venv/bin/python app --replication --run_minutely
             ├─50563 python /opt/raw-data-api/backend/replication update -s raw.lua --max-diff-size 10
             └─50704 osm2pgsql --append --slim --prefix planet_osm --output=flex --extra-attributes --style raw.lua -d app_backend -U adm_app_backend -H rawdat.postgres.database.azure.com >

Feb 13 14:30:03 raw-data-backend-production systemd[1]: Started Raw Data Backend Service.
Feb 13 14:30:04 raw-data-backend-production python[50562]: 2023-02-13 14:30:04 [INFO]: Initialised updates for service 'https://planet.openstreetmap.org/replication/minute'.
Feb 13 14:30:04 raw-data-backend-production python[50562]: 2023-02-13 14:30:04 [INFO]: Starting at sequence 5348603 (2022-12-06 00:59:10+00:00).
Feb 13 14:30:05 raw-data-backend-production python[50563]: 2023-02-13 14:30:05 [INFO]: Using replication service 'https://planet.openstreetmap.org/replication/minute'. Current sequence 5348603 (2>
Feb 13 14:30:10 raw-data-backend-production python[50704]: 2023-02-13 14:30:10  osm2pgsql version 1.6.0
Feb 13 14:30:10 raw-data-backend-production python[50704]: 2023-02-13 14:30:10  Database version: 14.6
Feb 13 14:30:10 raw-data-backend-production python[50704]: 2023-02-13 14:30:10  PostGIS version: 3.2

```

- Setup your every minute update timer 
```
$ sudo systemctl edit --full --force raw-data-backend.timer
```

```
[Unit]
Description=Trigger a rawdata database update

[Timer]
OnBootSec=10
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

- Enable timer and reload your systemctl

```
$ sudo systemctl enable raw-data-backend.timer
$ sudo systemctl daemon-reload
```
