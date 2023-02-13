## Getting Started

- Install [osm2pgsql >= v1.6.0](https://osm2pgsql.org/doc/install.html)
  ```
  sudo apt-get install osm2pgsql
  ```
- Clone rawdata and navigate to backend dir

  ```
  git clone https://github.com/hotosm/export-tool-api.git && cd backend
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

  To Run Replication only

  ```
  python raw_backend --replication
  ```

  > By Default this command will run replciation until data becomes up to date and die ! You can run this script on your custom frequency by specifying your cron / prefeered way to wake the script do the job and sleep

  Run Replication minutely

  ```
  python raw_backend --replication --run_minutely
  ```

  > This is another option to run the script and keep database up to date by running it minutely you can directly tell the script you want to run the app minutely. By this app will sleep for 60 sec before making another request and it will run forever until it is killed . You can simply enable this in your system

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
  --run_minutely        Runs replication every minute
  --country COUNTRY     ogc_fid of the country , if you are loading country , it will filter replication data
  --insert              Run osm2pgsql to insert data , Initial Creation Step
  --update              Run Update on table fields for country info
  --download_dir DOWNLOAD_DIR
                          The directory to download the source file to
  --post_index          Run Post index only on table
  ```

  If you are interested on Manual setup find Guide [here](./Manual.md)
