import json

from locust import HttpUser, task


class Raw(HttpUser):
    @task(1)
    def raw_data_request_geojson(self):
        """payload is of kathmandu area , Produces 146 MB of file. Usually takes 15-19 Sec to Generate. Does not uses ogr2ogr"""
        payload = {
            "fileName": "load_test",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.21270751953125, 27.646431146293423],
                        [85.49629211425781, 27.646431146293423],
                        [85.49629211425781, 27.762545086827302],
                        [85.21270751953125, 27.762545086827302],
                        [85.21270751953125, 27.646431146293423],
                    ]
                ],
            },
        }

        headers = {"content-type": "application/json"}

        self.client.post(
            "/raw-data/current-snapshot/", data=json.dumps(payload), headers=headers
        )

    @task(2)
    def raw_data_request_shapefile(self):
        """payload is of same area with shapefile option.Uses ogr2ogr , Produces 202MB of file and 25-30 Sec on single request"""
        payload = {
            "fileName": "load_test",
            "outputType": "shp",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.21270751953125, 27.646431146293423],
                        [85.49629211425781, 27.646431146293423],
                        [85.49629211425781, 27.762545086827302],
                        [85.21270751953125, 27.762545086827302],
                        [85.21270751953125, 27.646431146293423],
                    ]
                ],
            },
        }

        headers = {"content-type": "application/json"}

        self.client.post(
            "/raw-data/current-snapshot/", data=json.dumps(payload), headers=headers
        )
