Dev Setup Guide 

First things first : 
Create config.txt inside src folder like this 

Run underpass from here , by following the documentation or download dump from here to your database 

Setup insight from here or download schema from here 

Download dump of TM from here and setup in your database 

Now setup the config blocks with the database credentials where you have underpass ,insight and tm in your database

Inside config.txt put your credentials 

[INSIGHTS]
host=localhost
user=admin
password=admin
database=underpass
port=6060

[UNDERPASS]
host=localhost
user=admin
password=admin
database=insight
port=7070

[TM]
host=localhost
user=admin
password=admin
database=tm4snap
port=7070

Now setup oauth application for your local setup of API 
go to osm.org and in your profile page go to settings and register galaxy api as oauth 2 application and the get the secret key  client id and fill to the config.txt block like this , you can generate secret key for your application by yourself 

[OAUTH]
client_id= your client id 
client_secret= your client secret
url=https://www.openstreetmap.org
scope=read_prefs
login_redirect_uri=http://127.0.0.1:8000/auth/callback
secret_key=jnfdsjkfndsjkfnsdkjfnskfn

