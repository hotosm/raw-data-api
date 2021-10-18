import unittest
from osm_stats import functions
from configparser import ConfigParser


# with invalid database credentials  defined by developer
config = ConfigParser()
config.read("config.txt")

class MyTestCase(unittest.TestCase):
    # for simple function call with mapathon predefined set of key and value
    def test_mapathondefault(self):
        mapathonobj= functions.Mapathon()
        mapathonobj.getall_validation()


    def test_invaliddbparam(self):

        dbobj= functions.Database(dict(config.items("PG_INVALID")))
        dbobj.connect()

    # with invalid sql query provided by developer
    def test_invalidsqlquery(self):

        database= functions.Database(dict(config.items("PG")))
        database.connect()
        database.executequery(f"""
                    SELECT *
                    FROM dasfdasf           
                    """)


if __name__ == "__main__":
    unittest.main()




