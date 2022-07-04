import time, json
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(3, 5)

    @task(1)
    def raw_data_request_geojson(self):
      """payload is of kathmandu area , Produces 146 MB of file. Usually takes 15-19 Sec to Generate. Does not uses ogr2ogr"""
      payload = {
            "fileName": "load_test",
            'geometry': {
        "type": "Polygon",
        "coordinates": [
          [
            [
              85.21270751953125,
              27.646431146293423
            ],
            [
              85.49629211425781,
              27.646431146293423
            ],
            [
              85.49629211425781,
              27.762545086827302
            ],
            [
              85.21270751953125,
              27.762545086827302
            ],
            [
              85.21270751953125,
              27.646431146293423
            ]
          ]
        ]
      }
        }
        
      headers = {'content-type': 'application/json'}
        
      response = self.client.post("/raw-data/current-snapshot/", data=json.dumps(payload), headers=headers)
    
    @task(2)
    def raw_data_request_shapefile(self):
      """payload is of Big kathmandu area , Produces 340 MB of file. Usually takes 45 Sec to Generate.Uses ogr2ogr"""
      payload = {
        "fileName": "load_test",
        "outputType": "shp",
        "geometry":{
        "type": "Polygon",
        "coordinates": [
          [
            [
              85.21270751953125,
              27.646431146293423
            ],
            [
              85.49629211425781,
              27.646431146293423
            ],
            [
              85.49629211425781,
              27.762545086827302
            ],
            [
              85.21270751953125,
              27.762545086827302
            ],
            [
              85.21270751953125,
              27.646431146293423
            ]
          ]
        ]
      }
        }
        
      headers = {'content-type': 'application/json'}
        
      response = self.client.post("/raw-data/current-snapshot/", data=json.dumps(payload), headers=headers)