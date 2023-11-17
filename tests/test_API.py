import time

from fastapi.testclient import TestClient

from API.main import app

client = TestClient(app)


def test_status():
    response = client.get("/v1/status/")
    assert response.status_code == 200


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
    time.sleep(15)  # wait for worker to complete task
    response = client.get(f"/v1{track_link}")
    assert response.status_code == 200
    res = response.json()
    check_status = res["status"]
    assert check_status == "SUCCESS"


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
    time.sleep(15)  # wait for worker to complete task
    response = client.get(f"/v1{track_link}")
    assert response.status_code == 200
    res = response.json()
    check_status = res["status"]
    assert check_status == "SUCCESS"


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
    time.sleep(15)  # wait for worker to complete task
    response = client.get(f"/v1{track_link}")
    assert response.status_code == 200
    res = response.json()
    check_status = res["status"]
    assert check_status == "SUCCESS"


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
    time.sleep(15)  # wait for worker to complete task
    response = client.get(f"/v1{track_link}")
    assert response.status_code == 200
    res = response.json()
    check_status = res["status"]
    assert check_status == "SUCCESS"


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
