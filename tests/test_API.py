import os
import time

from fastapi.testclient import TestClient

from API.main import app

client = TestClient(app)

access_token = os.environ.get("ACCESS_TOKEN")

## Status


def wait_for_task_completion(track_link, max_attempts=12, interval_seconds=5):
    """
    Waits for a task to complete, polling the task status at specified intervals.

    :param track_link: The endpoint to check the task status.
    :param max_attempts: Maximum number of polling attempts.
    :param interval_seconds: Time to wait between each polling attempt.
    :return: The final response JSON on success or raises an AssertionError on failure.
    """
    for attempt in range(1, max_attempts + 1):
        time.sleep(interval_seconds)  # wait for the worker to complete the task

        response = client.get(f"/v1{track_link}")
        assert response.status_code == 200, "Task status check failed"
        res = response.json()
        check_status = res["status"]

        if check_status == "SUCCESS":
            return res  # Task completed successfully

        if attempt == max_attempts:
            raise AssertionError(
                f"Task did not complete successfully after {max_attempts} attempts with following response {res}"
            )


def test_status():
    response = client.get("/v1/status/")
    assert response.status_code == 200


## Login
def test_login_url():
    response = client.get("/v1/auth/login/")
    assert response.status_code == 200


def test_login_auth_me():
    headers = {"access-token": access_token}
    response = client.get("/v1/auth/me/", headers=headers)
    assert response.status_code == 200


## Countries


def test_countries_endpoint():
    response = client.get("/v1/countries/?q=nepal")
    assert response.status_code == 200


## test osm_id


def test_osm_id_endpoint():
    response = client.get("/v1/osm_id/?osm_id=421498318")
    assert response.status_code == 200


## Snapshot
def test_snapshot():
    response = client.post(
        "/v1/snapshot/",
        json={
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [83.96919250488281, 28.194446860487773],
                        [83.99751663208006, 28.194446860487773],
                        [83.99751663208006, 28.214869548073377],
                        [83.96919250488281, 28.214869548073377],
                        [83.96919250488281, 28.194446860487773],
                    ]
                ],
            }
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_featurecollection():
    response = client.post(
        "/v1/snapshot/",
        json={
            "geometry": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "coordinates": [
                                [
                                    [83.97346137271688, 28.217525272345284],
                                    [83.97346137271688, 28.192595937414737],
                                    [84.01473909818759, 28.192595937414737],
                                    [84.01473909818759, 28.217525272345284],
                                    [83.97346137271688, 28.217525272345284],
                                ]
                            ],
                            "type": "Polygon",
                        },
                    }
                ],
            }
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_feature():
    response = client.post(
        "/v1/snapshot/",
        json={
            "geometry": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "coordinates": [
                        [
                            [83.97346137271688, 28.217525272345284],
                            [83.97346137271688, 28.192595937414737],
                            [84.01473909818759, 28.192595937414737],
                            [84.01473909818759, 28.217525272345284],
                            [83.97346137271688, 28.217525272345284],
                        ]
                    ],
                    "type": "Polygon",
                },
            }
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_feature_fgb_wrap_geom():
    response = client.post(
        "/v1/snapshot/",
        json={
            "fgbWrapGeoms": True,
            "outputType": "fgb",
            "geometry": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "coordinates": [
                        [
                            [83.97346137271688, 28.217525272345284],
                            [83.97346137271688, 28.192595937414737],
                            [84.01473909818759, 28.192595937414737],
                            [84.01473909818759, 28.217525272345284],
                            [83.97346137271688, 28.217525272345284],
                        ]
                    ],
                    "type": "Polygon",
                },
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_centroid():
    response = client.post(
        "/v1/snapshot/",
        json={
            "centroid": True,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [83.96919250488281, 28.194446860487773],
                        [83.99751663208006, 28.194446860487773],
                        [83.99751663208006, 28.214869548073377],
                        [83.96919250488281, 28.214869548073377],
                        [83.96919250488281, 28.194446860487773],
                    ]
                ],
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_filters():
    response = client.post(
        "/v1/snapshot/",
        json={
            "fileName": "Example export with all features",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [83.585701, 28.046607],
                        [83.585701, 28.382561],
                        [84.391823, 28.382561],
                        [84.391823, 28.046607],
                        [83.585701, 28.046607],
                    ]
                ],
            },
            "outputType": "geojson",
            "geometryType": ["point", "line", "polygon"],
            "filters": {
                "tags": {
                    "point": {
                        "join_or": {
                            "amenity": [
                                "bank",
                                "ferry_terminal",
                                "bus_station",
                                "fuel",
                                "kindergarten",
                                "school",
                                "college",
                                "university",
                                "place_of_worship",
                                "marketplace",
                                "clinic",
                                "hospital",
                                "police",
                                "fire_station",
                            ],
                            "building": [
                                "bank",
                                "aerodrome",
                                "ferry_terminal",
                                "train_station",
                                "bus_station",
                                "pumping_station",
                                "power_substation",
                                "kindergarten",
                                "school",
                                "college",
                                "university",
                                "mosque ",
                                " church ",
                                " temple",
                                "supermarket",
                                "marketplace",
                                "clinic",
                                "hospital",
                                "police",
                                "fire_station",
                                "stadium ",
                                " sports_centre",
                                "governor_office ",
                                " townhall ",
                                " subdistrict_office ",
                                " village_office ",
                                " community_group_office",
                                "government_office",
                            ],
                            "man_made": ["tower", "water_tower", "pumping_station"],
                            "tower:type": ["communication"],
                            "aeroway": ["aerodrome"],
                            "railway": ["station"],
                            "emergency": ["fire_hydrant"],
                            "landuse": ["reservoir", "recreation_gound"],
                            "waterway": ["floodgate"],
                            "natural": ["spring"],
                            "power": ["tower", "substation"],
                            "shop": ["supermarket"],
                            "leisure": [
                                "stadium ",
                                " sports_centre ",
                                " pitch ",
                                " swimming_pool",
                                "park",
                            ],
                            "office": ["government"],
                        }
                    },
                    "line": {
                        "join_or": {
                            "highway": [
                                "motorway ",
                                " trunk ",
                                " primary ",
                                " secondary ",
                                " tertiary ",
                                " service ",
                                " residential ",
                                " pedestrian ",
                                " path ",
                                " living_street ",
                                " track",
                            ],
                            "railway": ["rail"],
                            "man_made": ["embankment"],
                            "waterway": [],
                        }
                    },
                    "polygon": {
                        "join_or": {
                            "amenity": [
                                "bank",
                                "ferry_terminal",
                                "bus_station",
                                "fuel",
                                "kindergarten",
                                "school",
                                "college",
                                "university",
                                "place_of_worship",
                                "marketplace",
                                "clinic",
                                "hospital",
                                "police",
                                "fire_station",
                            ],
                            "building": [
                                "bank",
                                "aerodrome",
                                "ferry_terminal",
                                "train_station",
                                "bus_station",
                                "pumping_station",
                                "power_substation",
                                "power_plant",
                                "kindergarten",
                                "school",
                                "college",
                                "university",
                                "mosque ",
                                " church ",
                                " temple",
                                "supermarket",
                                "marketplace",
                                "clinic",
                                "hospital",
                                "police",
                                "fire_station",
                                "stadium ",
                                " sports_centre",
                                "governor_office ",
                                " townhall ",
                                " subdistrict_office ",
                                " village_office ",
                                " community_group_office",
                                "government_office",
                            ],
                            "man_made": ["tower", "water_tower", "pumping_station"],
                            "tower:type": ["communication"],
                            "aeroway": ["aerodrome"],
                            "railway": ["station"],
                            "landuse": ["reservoir", "recreation_gound"],
                            "waterway": [],
                            "natural": ["spring"],
                            "power": ["substation", "plant"],
                            "shop": ["supermarket"],
                            "leisure": [
                                "stadium ",
                                " sports_centre ",
                                " pitch ",
                                " swimming_pool",
                                "park",
                            ],
                            "office": ["government"],
                            "type": ["boundary"],
                            "boundary": ["administrative"],
                        },
                    },
                },
                "attributes": {
                    "point": [
                        "building",
                        "ground_floor:height",
                        "capacity:persons",
                        "building:structure",
                        "building:condition",
                        "name",
                        "admin_level",
                        "building:material",
                        "office",
                        "building:roof",
                        "backup_generator",
                        "access:roof",
                        "building:levels",
                        "building:floor",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "line": ["width", "source", "waterway", "name"],
                    "polygon": [
                        "landslide_prone",
                        "name",
                        "admin_level",
                        "type",
                        "is_in:town",
                        "flood_prone",
                        "is_in:province",
                        "is_in:city",
                        "is_in:municipality",
                        "is_in:RW",
                        "is_in:village",
                        "source",
                        "boundary",
                    ],
                },
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_and_filter():
    response = client.post(
        "/v1/snapshot/",
        json={
            "fileName": "Destroyed_Buildings_Turkey",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [36.70588085657477, 37.1979648807274],
                        [36.70588085657477, 37.1651408422983],
                        [36.759267544807194, 37.1651408422983],
                        [36.759267544807194, 37.1979648807274],
                        [36.70588085657477, 37.1979648807274],
                    ]
                ],
            },
            "outputType": "geojson",
            "geometryType": ["polygon"],
            "filters": {
                "tags": {
                    "point": {},
                    "line": {},
                    "polygon": {
                        "join_or": {},
                        "join_and": {
                            "destroyed:building": ["yes"],
                            "damage:date": ["2023-02-06"],
                        },
                    },
                },
                "attributes": {
                    "point": [],
                    "line": [],
                    "polygon": [
                        "building",
                        "destroyed:building",
                        "damage:date",
                        "name",
                        "source",
                    ],
                },
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_authentication_uuid():
    headers = {"access-token": access_token}
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.96919250488281, 28.194446860487773],
                    [83.99751663208006, 28.194446860487773],
                    [83.99751663208006, 28.214869548073377],
                    [83.96919250488281, 28.214869548073377],
                    [83.96919250488281, 28.194446860487773],
                ]
            ],
        },
        "uuid": False,
    }

    response = client.post("/v1/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_snapshot_bind_zip():
    headers = {"access-token": access_token}
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.96919250488281, 28.194446860487773],
                    [83.99751663208006, 28.194446860487773],
                    [83.99751663208006, 28.214869548073377],
                    [83.96919250488281, 28.214869548073377],
                    [83.96919250488281, 28.194446860487773],
                ]
            ],
        },
        "bindZip": False,
    }

    response = client.post("/v1/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


## Snapshot Plain


def test_snapshot_plain():
    response = client.post(
        "/v1/snapshot/plain/",
        json={
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [83.96919250488281, 28.194446860487773],
                        [83.99751663208006, 28.194446860487773],
                        [83.99751663208006, 28.214869548073377],
                        [83.96919250488281, 28.214869548073377],
                        [83.96919250488281, 28.194446860487773],
                    ]
                ],
            }
        },
    )
    assert response.status_code == 200


## Stats


def test_stats_endpoint_custom_polygon():
    headers = {"access-token": access_token}
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.96919250488281, 28.194446860487773],
                    [83.99751663208006, 28.194446860487773],
                    [83.99751663208006, 28.214869548073377],
                    [83.96919250488281, 28.214869548073377],
                    [83.96919250488281, 28.194446860487773],
                ]
            ],
        }
    }

    response = client.post("/v1/stats/polygon/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    assert (
        res["meta"]["indicators"]
        == "https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md"
    )


def test_stats_endpoint_iso3():
    headers = {"access-token": access_token}
    payload = {"iso3": "npl"}

    response = client.post("/v1/stats/polygon/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    assert (
        res["meta"]["indicators"]
        == "https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md"
    )


# HDX


def test_hdx_submit_normal_iso3():
    headers = {"access-token": access_token}
    payload = {
        "iso3": "NPL",
        "hdx_upload": False,
        "categories": [
            {
                "Roads": {
                    "hdx": {
                        "tags": ["roads", "transportation", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines"],
                    "select": ["name", "highway"],
                    "where": "tags['highway'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            }
        ],
    }

    response = client.post("/v1/custom/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_hdx_submit_normal_iso3_multiple_format():
    headers = {"access-token": access_token}
    payload = {
        "iso3": "NPL",
        "hdx_upload": False,
        "categories": [
            {
                "Roads": {
                    "hdx": {
                        "tags": ["roads", "transportation", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines"],
                    "select": ["name", "highway"],
                    "where": "tags['highway'] IS NOT NULL",
                    "formats": ["geojson", "gpkg", "kml", "shp"],
                }
            }
        ],
    }

    response = client.post("/v1/custom/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_hdx_submit_normal_custom_polygon():
    headers = {"access-token": access_token}
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.96919250488281, 28.194446860487773],
                    [83.99751663208006, 28.194446860487773],
                    [83.99751663208006, 28.214869548073377],
                    [83.96919250488281, 28.214869548073377],
                    [83.96919250488281, 28.194446860487773],
                ]
            ],
        },
        "hdx_upload": False,
        "dataset": {
            "subnational": True,
            "dataset_title": "Pokhara",
            "dataset_prefix": "hotosm_pkr",
            "dataset_locations": ["npl"],
        },
        "categories": [
            {
                "Roads": {
                    "hdx": {
                        "tags": ["roads", "transportation", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines"],
                    "select": ["name", "highway"],
                    "where": "tags['highway'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            }
        ],
    }

    response = client.post("/v1/custom/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_custom_submit_normal_custom_polygon_TM_project():
    headers = {"access-token": access_token}
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.96919250488281, 28.194446860487773],
                    [83.99751663208006, 28.194446860487773],
                    [83.99751663208006, 28.214869548073377],
                    [83.96919250488281, 28.214869548073377],
                    [83.96919250488281, 28.194446860487773],
                ]
            ],
        },
        "queue": "raw_ondemand",
        "dataset": {
            "dataset_prefix": "hotosm_project_1",
            "dataset_folder": "TM",
            "dataset_title": "Tasking Manger Project 1",
        },
        "categories": [
            {
                "Buildings": {
                    "types": ["polygons"],
                    "select": [
                        "name",
                        "building",
                        "building:levels",
                        "building:materials",
                        "addr:full",
                        "addr:housenumber",
                        "addr:street",
                        "addr:city",
                        "office",
                        "source",
                    ],
                    "where": "tags['building'] IS NOT NULL",
                    "formats": ["geojson", "shp", "kml"],
                },
                "Roads": {
                    "types": ["lines"],
                    "select": [
                        "name",
                        "highway",
                        "surface",
                        "smoothness",
                        "width",
                        "lanes",
                        "oneway",
                        "bridge",
                        "layer",
                        "source",
                    ],
                    "where": "tags['highway'] IS NOT NULL",
                    "formats": ["geojson", "shp", "kml"],
                },
                "Waterways": {
                    "types": ["lines", "polygons"],
                    "select": [
                        "name",
                        "waterway",
                        "covered",
                        "width",
                        "depth",
                        "layer",
                        "blockage",
                        "tunnel",
                        "natural",
                        "water",
                        "source",
                    ],
                    "where": "tags['waterway'] IS NOT NULL OR tags['water'] IS NOT NULL OR tags['natural'] IN ('water','wetland','bay')",
                    "formats": ["geojson", "shp", "kml"],
                },
                "Landuse": {
                    "types": ["points", "polygons"],
                    "select": ["name", "amenity", "landuse", "leisure"],
                    "where": "tags['landuse'] IS NOT NULL",
                    "formats": ["geojson", "shp", "kml"],
                },
            }
        ],
    }

    response = client.post("/v1/custom/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_hdx_submit_normal_custom_polygon_upload():
    headers = {"access-token": access_token}
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [83.96919250488281, 28.194446860487773],
                    [83.99751663208006, 28.194446860487773],
                    [83.99751663208006, 28.214869548073377],
                    [83.96919250488281, 28.214869548073377],
                    [83.96919250488281, 28.194446860487773],
                ]
            ],
        },
        "hdx_upload": True,
        "dataset": {
            "subnational": True,
            "dataset_title": "Pokhara",
            "dataset_folder": "Test",
            "dataset_prefix": "hotosm_pkr",
            "dataset_locations": ["npl"],
        },
        "categories": [
            {
                "Roads": {
                    "hdx": {
                        "tags": ["roads", "transportation", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines"],
                    "select": ["name", "highway"],
                    "where": "tags['highway'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            }
        ],
    }

    response = client.post("/v1/custom/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


def test_full_hdx_set_iso():
    headers = {"access-token": access_token}
    payload = {
        "iso3": "NPL",
        "hdx_upload": False,
        "categories": [
            {
                "Buildings": {
                    "hdx": {
                        "tags": [
                            "facilities-infrastructure",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["polygons"],
                    "select": [
                        "name",
                        "building",
                        "building:levels",
                        "building:materials",
                        "addr:full",
                        "addr:housenumber",
                        "addr:street",
                        "addr:city",
                        "office",
                        "source",
                    ],
                    "where": "tags['building'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            },
            {
                "Roads": {
                    "hdx": {
                        "tags": ["transportation", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines"],
                    "select": [
                        "name",
                        "highway",
                        "surface",
                        "smoothness",
                        "width",
                        "lanes",
                        "oneway",
                        "bridge",
                        "layer",
                        "source",
                    ],
                    "where": "tags['highway'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            },
            {
                "Waterways": {
                    "hdx": {
                        "tags": ["hydrology", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines", "polygons"],
                    "select": [
                        "name",
                        "waterway",
                        "covered",
                        "width",
                        "depth",
                        "layer",
                        "blockage",
                        "tunnel",
                        "natural",
                        "water",
                        "source",
                    ],
                    "where": "tags['waterway'] IS NOT NULL OR tags['water'] IS NOT NULL OR tags['natural'] IN ('water','wetland','bay')",
                    "formats": ["geojson"],
                }
            },
            {
                "Points of Interest": {
                    "hdx": {
                        "tags": [
                            "facilities-infrastructure",
                            "points of interest-poi",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points", "polygons"],
                    "select": [
                        "name",
                        "amenity",
                        "man_made",
                        "shop",
                        "tourism",
                        "opening_hours",
                        "beds",
                        "rooms",
                        "addr:full",
                        "addr:housenumber",
                        "addr:street",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['amenity'] IS NOT NULL OR tags['man_made'] IS NOT NULL OR tags['shop'] IS NOT NULL OR tags['tourism'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            },
            {
                "Airports": {
                    "hdx": {
                        "tags": [
                            "aviation",
                            "facilities-infrastructure",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points", "lines", "polygons"],
                    "select": [
                        "name",
                        "aeroway",
                        "building",
                        "emergency",
                        "emergency:helipad",
                        "operator:type",
                        "capacity:persons",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['aeroway'] IS NOT NULL OR tags['building'] = 'aerodrome' OR tags['emergency:helipad'] IS NOT NULL OR tags['emergency'] = 'landing_site'",
                    "formats": ["geojson"],
                }
            },
            {
                "Sea Ports": {
                    "hdx": {
                        "tags": [
                            "facilities-infrastructure",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points", "lines", "polygons"],
                    "select": [
                        "name",
                        "amenity",
                        "building",
                        "port",
                        "operator:type",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['amenity'] = 'ferry_terminal' OR tags['building'] = 'ferry_terminal' OR tags['port'] IS NOT NULL",
                    "formats": ["geojson"],
                }
            },
            {
                "Education Facilities": {
                    "hdx": {
                        "tags": [
                            "education facilities-schools",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points", "polygons"],
                    "select": [
                        "name",
                        "amenity",
                        "building",
                        "operator:type",
                        "capacity:persons",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['amenity'] IN ('kindergarten', 'school', 'college', 'university') OR tags['building'] IN ('kindergarten', 'school', 'college', 'university')",
                    "formats": ["geojson"],
                }
            },
            {
                "Health Facilities": {
                    "hdx": {
                        "tags": ["geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points", "polygons"],
                    "select": [
                        "name",
                        "amenity",
                        "building",
                        "healthcare",
                        "healthcare:speciality",
                        "operator:type",
                        "capacity:persons",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['healthcare'] IS NOT NULL OR tags['amenity'] IN ('doctors', 'dentist', 'clinic', 'hospital', 'pharmacy')",
                    "formats": ["geojson"],
                }
            },
            {
                "Populated Places": {
                    "hdx": {
                        "tags": [
                            "populated places-settlements",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points"],
                    "select": [
                        "name",
                        "place",
                        "population",
                        "is_in",
                        "source",
                    ],
                    "where": "tags['place'] IN ('isolated_dwelling', 'town', 'village', 'hamlet', 'city')",
                    "formats": ["geojson"],
                }
            },
            {
                "Financial Services": {
                    "hdx": {
                        "tags": ["economics", "geodata"],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["points", "polygons"],
                    "select": [
                        "name",
                        "amenity",
                        "operator",
                        "network",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['amenity'] IN ('mobile_money_agent','bureau_de_change','bank','microfinance','atm','sacco','money_transfer','post_office')",
                    "formats": ["geojson"],
                }
            },
            {
                "Railways": {
                    "hdx": {
                        "tags": [
                            "facilities-infrastructure",
                            "railways",
                            "transportation",
                            "geodata",
                        ],
                        "caveats": "OpenStreetMap data is crowd sourced and cannot be considered to be exhaustive",
                    },
                    "types": ["lines"],
                    "select": [
                        "name",
                        "railway",
                        "ele",
                        "operator:type",
                        "layer",
                        "addr:full",
                        "addr:city",
                        "source",
                    ],
                    "where": "tags['railway'] IN ('rail','station')",
                    "formats": ["geojson"],
                }
            },
        ],
    }

    response = client.post("/v1/custom/snapshot/", json=payload, headers=headers)

    assert response.status_code == 200
    res = response.json()
    track_link = res["track_link"]
    wait_for_task_completion(track_link)


# ## Tasks connection


def test_worker_connection():
    response = client.get("/v1/tasks/ping/")
    assert response.status_code == 200
