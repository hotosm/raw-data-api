import unittest
from osm_stats import functions
from configparser import ConfigParser

config = ConfigParser()
config.read("config.txt")

class testdb(unittest.TestCase):

    def setUp(self):
        self.database= functions.Database(dict(config.items("PG")))

    def test_connection(self):
        self.database= functions.Database(dict(config.items("PG")))
        self.database.connect()

    def test_runquery(self):
        self.database.connect()
        query=f"""
                SELECT *
                FROM validation           
                """
        self.database.executequery(query)

    # def tearDown(self):
    #     self.database.stop()
        
if __name__ == '__main__':
    
    unittest.main()

        