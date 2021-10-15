
from osm_stats import functions
from configparser import ConfigParser

# for simple function call with mapathon predefined set of key and value
def mapathondefault():
    mapathonobj= functions.Mapathon()
    mapathonobj.getall_validation()

# with invalid database credentials  defined by developer
config = ConfigParser()
config.read("config.txt")

def invaliddbparam():

    dbobj= functions.Database(dict(config.items("PG_INVALID")))
    dbobj.connect()

# with invalid sql query provided by developer
def invalidsqlquery():

    database= functions.Database(dict(config.items("PG")))
    database.connect()
    database.executequery(f"""
                SELECT *
                FROM dasfdasf           
                """)


mapathondefault()
invaliddbparam()
invalidsqlquery()