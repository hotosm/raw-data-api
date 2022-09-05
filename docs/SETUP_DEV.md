Dev Setup Guide 

First things first : 

## Install

#### 1. Install requirements.

Install gdal on your machine , for example on Ubuntu

```
sudo apt-add-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev
```

Clone the Repo to your machine 

``` git clone https://github.com/hotosm/galaxy-api.git ```

Navigate to repo 

``` cd galaxy-api ```

Install python dependencies

```pip install -r requirements.txt```

Install gdal python ( Include your gdal version , if you are using different version ) 
 
```pip install gdal==3.0.2```



#### 2. Create ```config.txt``` inside src directory.
![image](https://user-images.githubusercontent.com/36752999/188402566-80dc9633-5d4e-479c-97dc-9e8a4999b385.png)


#### 3. Setup Underpass 
  Run underpass from [here](https://github.com/hotosm/underpass/blob/master/doc/getting-started.md) by following the          documentation  or Create database "underpass" in your local postgres and insert sample dump from  ```/tests/src/fixtures/underpass.sql ```

#### 4. Setup Insights 
Setup insights from [here](https://github.com/hotosm/insights) or Create database "insights" in your local postgres and insert sample dump from  ```/tests/src/fixtures/insights.sql ```

#### 5. Setup Raw Data  
Initialize rawdata from [here](https://github.com/hotosm/underpass/tree/master/raw) or Create database "raw" in your local postgres and insert sample dump from  ```/tests/src/fixtures/raw_data.sql ```

#### 6. Setup Tasking Manager Dump 
Download dump of TM from here and setup in your database 

#### 7. Put your credentials inside config.txt
Insert your config blocks with the database credentials where you have underpass ,insight and tm in your database

```
[INSIGHTS]
host=localhost
user=postgres
password=admin
database=underpass
port=5432

[UNDERPASS]
host=localhost
user=postgres
password=admin
database=insight
port=5432

[RAW_DATA]
host=localhost
user=postgres
password=admin
database=raw
port=5432

[TM]
host=
user=
password=
port=
```

#### 8. Setup Oauth 
Login to osm.org , Click on My Settings and register your local galaxy app to Oauth2applications
![image](https://user-images.githubusercontent.com/36752999/188406664-371e4353-088c-4608-9761-7b652d4e396c.png)

Check on read user preferences and Enter redirect URI as following
```http://127.0.0.1:8000/latest/auth/callback/```

Grab Client ID and Client Secret and put it inside config.txt as OAUTH Block , you can generate secret key for your application by yourself
```
[OAUTH]
client_id= your client id 
client_secret= your client secret
url=https://www.openstreetmap.org
scope=read_prefs
login_redirect_uri=http://127.0.0.1:8000/auth/callback/
secret_key=jnfdsjkfndsjkfnsdkjfnskfn

```



