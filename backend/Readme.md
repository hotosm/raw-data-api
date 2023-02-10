## Getting Started 

- Install [osm2pgsql > v1.6.0](https://osm2pgsql.org/doc/install.html)
    ```
    sudo apt-get install osm2pgsql
    ```
- Clone rawdata and navigate to backend dir
    ```
    git clone https://github.com/hotosm/export-tool-api.git && cd backend
    ```

- Install Requirements

    Install [psycopg2](https://pypi.org/project/psycopg2/), [osmium](https://pypi.org/project/osmium/) and [dateutil](https://pypi.org/project/python-dateutil/) , wget in your python env . You can install using ```requirements.txt``` too 

    ```
    pip install -r requirements.txt
    ```

 - Start the Process

    You can either export your db params as env variables or pass to script 
    ```
    export PGHOST=localhost
    export PGPORT=5432
    export PGUSER=admin
    export PGPASSWORD=admin
    export PGDATABASE=postgres
    ```
    Run App , For Insert 
    ```
    python app --insert --replication
    ```

    Only start replication 

    ```
    python app --replication
    ```
    Run Replication minutely 
    ```
    python app --replication --run_minutely
    ```

    Options : 
    
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
    --country COUNTRY     Fid of the country , if you are loading country , it will filter replication data
    --insert              Run osm2pgsql to insert data , Initial Creation Step
    --update              Run Update on table fields for country info
    --download_dir DOWNLOAD_DIR
                            The directory to download the source file to
    --post_index          Run Post index only on table
    ```


    >You can Download Planet pbf file [Here](https://planet.osm.org/pbf/) or Use Geofabrik Pbf file [Here](https://osm-internal.download.geofabrik.de/index.html) with full metadata (Tested with .pbf file) , you can pass download link to script itself . Follow -h help

    If you are interested on Manual setup find Guide [here](./Manual.md) 
