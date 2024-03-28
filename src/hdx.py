"""
hdx.py
"""

import logging
import os
import json
from datetime import datetime
from slugify import slugify

from postgres import AsyncPostgres
from s3 import AsyncS3FileTransfer

HDX_URL_PREFIX = "https://data.humdata.org"
HDX_FILTER_CRITERIA = """
The OpenStreetMap (OSM) data categories listed below have been filtered using the following criteria:

- `{criteria}`

"""

HDX_MARKDOWN = """
The OSM attributes extracted for each dataset are listed below:
{columns}

{filter_str}
"""

HDX_OWNER_ORG = "84add935-473b-4e44-8613-80a9afdb6e53"
HDX_MAINTAINER = "196196be-6037-4488-8b71-d786adf4c081"


class HDXUploader:
    """
    Constructor for the HDXUploader class.

    Parameters:
    - category (Dict[str, CategoryModel]): Dictionary representing a category.
    - hdx (HDX): Instance of the HDX class.
    - uuid (str): Universally unique identifier.
    - default_category_path (str): Default path for the category.
    - completeness_metadata (Optional[Dict[str, Any]]): Metadata for completeness.
    """

    def __init__(
        self, category, hdx, uuid, default_category_path, completeness_metadata=None
    ):
        self.hdx = hdx
        self.category_name, self.category_data = list(category.items())[0]
        self.category_path = os.path.join(
            default_category_path, slugify(self.category_name.lower()).replace("-", "_")
        )
        self.dataset = None
        self.uuid = uuid
        self.completeness_metadata = completeness_metadata
        self.data_completeness_stats = None
        self.resources = []

    def slugify(self, name):
        """
        Converts a string to a valid slug format.

        Parameters:
        - name (str): Input string.

        Returns:
        - Slugified string.
        """
        return slugify(name).replace("-", "_")

    def add_notes(self):
        """
        Adds notes based on category data.

        Returns:
        - Notes string.
        """
        columns = []
        for key in self.category_data.select:
            columns.append(
                "- [{0}](http://wiki.openstreetmap.org/wiki/Key:{0})".format(key)
            )
        columns = "\n".join(columns)
        filter_str = HDX_FILTER_CRITERIA.format(criteria=self.category_data.where)
        if self.category_name.lower() in ["roads", "buildings"]:
            if self.data_completeness_stats is None:
                if self.completeness_metadata:
                    self.data_completeness_stats = PolygonStats(
                        iso3=self.completeness_metadata["iso3"],
                        geojson=(
                            self.completeness_metadata["geometry"]
                            if self.completeness_metadata["geometry"]
                            else None
                        ),
                    ).get_summary_stats()
            if self.data_completeness_stats:
                self.category_data.hdx.notes += f'{self.data_completeness_stats["summary"][self.category_name.lower()]}\n'
                self.category_data.hdx.notes += "Read about what this summary means : [indicators](https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/indicators.md) , [metrics](https://github.com/hotosm/raw-data-api/tree/develop/docs/src/stats/metrics.md)\n"

        return self.category_data.hdx.notes + HDX_MARKDOWN.format(
            columns=columns, filter_str=filter_str
        )

    async def add_resource(self, resource_meta):
        """
        Adds a resource to the list of resources.

        Parameters:
        - resource_meta (Dict[str, Any]): Metadata for the resource.
        """
        if self.dataset:
            self.resources.append(resource_meta)
            resource_obj = Resource(resource_meta)
            resource_obj.mark_data_updated()
            self.dataset.add_update_resource(resource_obj)

    async def upload_dataset(self, dump_config_to_s3=False):
        """
        Uploads the dataset to HDX.

        Parameters:
        - dump_config_to_s3 (bool): Flag to indicate whether to dump configuration to S3.

        Returns:
        - Tuple containing category name and dataset information.
        """
        if self.dataset:
            dataset_info = {}
            dt_config_path = os.path.join(
                self.category_path, f"{self.dataset['name']}_config.json"
            )
            self.dataset.save_to_json(dt_config_path)
            if dump_config_to_s3:
                s3_transfer = AsyncS3FileTransfer()
                s3_upload_name = os.path.relpath(
                    dt_config_path, os.path.join(export_path, self.uuid)
                )
                dataset_info["config"] = await s3_transfer.upload(
                    dt_config_path,
                    str(s3_upload_name),
                )

            self.dataset.set_time_period(datetime.now())
            try:
                self.dataset.create_in_hdx(
                    allow_no_resources=True,
                    hxl_update=False,
                )
                dataset_info["hdx_upload"] = "SUCCESS"
            except Exception as ex:
                logging.error(ex)
                dataset_info["hdx_upload"] = "FAILED"

            dataset_info["name"] = self.dataset["name"]
            dataset_info["hdx_url"] = f"{HDX_URL_PREFIX}/dataset/{self.dataset['name']}"
            dataset_info["resources"] = self.resources
            return self.category_name, dataset_info

    def init_dataset(self):
        """
        Initializes the HDX dataset.
        """
        dataset_prefix = self.hdx.dataset_prefix
        dataset_title = self.hdx.dataset_title
        dataset_locations = self.hdx.dataset_locations
        self.dataset = Dataset(
            {
                "name": "{0}_{1}".format(
                    dataset_prefix, self.slugify(self.category_name)
                ),
                "title": "{0} {1} (OpenStreetMap Export)".format(
                    dataset_title, self.category_name
                ),
                "owner_org": HDX_OWNER_ORG,
                "maintainer": HDX_MAINTAINER,
                "dataset_source": "OpenStreetMap contributors",
                "methodology": "Other",
                "methodology_other": "Volunteered geographic information",
                "license_id": "hdx-odc-odbl",
                "updated_by_script": f'Hotosm OSM Exports ({datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})',
                "caveats": self.category_data.hdx.caveats,
                "private": self.hdx.private,
                "notes": self.add_notes(),
                "subnational": 1 if self.hdx.subnational else 0,
            }
        )
        self.dataset.set_expected_update_frequency(self.hdx.update_frequency)
        for location in dataset_locations:
            self.dataset.add_other_location(location)
        for tag in self.category_data.hdx.tags:
            self.dataset.add_tag(tag)


class HDX:
    def __init__(self) -> None:
        """
        Initializes an instance of the HDX class, connecting to the database.
        """
        dbdict = get_db_connection_params()
        self.db = AsyncPostgres(dbdict)
        await self.db.establish_pool()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close_pool()  # Release the connection pool

    async def create_hdx(self, hdx_data):
        """
        Create a new HDX entry in the database.

        Args:
            hdx_data (dict): Data for creating the HDX entry.

        Returns:
            dict: Result of the HDX creation process.
        """
        insert_query = sql.SQL(
            """
            INSERT INTO public.hdx (iso3, hdx_upload, dataset, queue, meta, categories, geometry)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        )
        await self.db.execute(
            insert_query,
            (
                hdx_data.get("iso3", None),
                hdx_data.get("hdx_upload", True),
                json.dumps(hdx_data.get("dataset")),
                hdx_data.get("queue", "raw_ondemand"),
                hdx_data.get("meta", False),
                json.dumps(hdx_data.get("categories", {})),
                json.dumps(hdx_data.get("geometry")),
            ),
        )
        result = await self.db.fetchone()
        if result:
            return {"create": True}
        raise HTTPException(status_code=500, detail="Insert failed")

    async def get_hdx_list_with_filters(
        self, skip: int = 0, limit: int = 10, filters: dict = {}
    ):
        """
        Retrieve a list of HDX entries based on provided filters.

        Args:
            skip (int): Number of entries to skip.
            limit (int): Maximum number of entries to retrieve.
            filters (dict): Filtering criteria.

        Returns:
            List[dict]: List of HDX entries.
        """
        filter_conditions = []
        filter_values = []

        for key, value in filters.items():
            filter_conditions.append(key)
            filter_values.append(value)

        where_clause = " AND ".join(filter_conditions)

        select_query = sql.SQL(
            f"""
            SELECT ST_AsGeoJSON(c.*) FROM public.hdx c
            {"WHERE " + where_clause if where_clause else ""}
            OFFSET %s LIMIT %s
        """
        )

        result = await self.db.fetch(select_query, *filter_values, skip, limit)
        return [orjson.loads(item[0]) for item in result]

    async def search_hdx_by_dataset_title(
        self, dataset_title: str, skip: int = 0, limit: int = 10
    ):
        """
        Search for HDX entries by dataset title.

        Args:
            dataset_title (str): The title of the dataset to search for.
            skip (int): Number of entries to skip.
            limit (int): Maximum number of entries to retrieve.

        Returns:
            List[dict]: List of HDX entries matching the dataset title.
        """
        search_query = sql.SQL(
            """
            SELECT ST_AsGeoJSON(c.*) FROM public.hdx c
            WHERE c.dataset->>'dataset_title' ILIKE %s
            OFFSET %s LIMIT %s
            """
        )
        result = await self.db.fetch(search_query, "%" + dataset_title + "%", skip, limit)
        return [orjson.loads(item[0]) for item in result]

    async def get_hdx_by_id(self, hdx_id: int):
        """
        Retrieve a specific HDX entry by its ID.

        Args:
            hdx_id (int): ID of the HDX entry to retrieve.

        Returns:
            dict: Details of the requested HDX entry.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        select_query = sql.SQL(
            """
            SELECT ST_AsGeoJSON(c.*) FROM public.hdx c
            WHERE id = %s
        """
        )
        result = await self.db.fetchrow(select_query, hdx_id)
        if result:
            return orjson.loads(result[0])
        raise HTTPException(status_code=404, detail="Item not found")

    async def update_hdx(self, hdx_id: int, hdx_data):
        """
        Update an existing HDX entry in the database.

        Args:
            hdx_id (int): ID of the HDX entry to update.
            hdx_data (dict): Data for updating the HDX entry.

        Returns:
            dict: Result of the HDX update process.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        update_query = sql.SQL(
            """
            UPDATE public.hdx
            SET iso3 = %s, hdx_upload = %s, dataset = %s, queue = %s, meta = %s, categories = %s, geometry = %s
            WHERE id = %s
            RETURNING *
        """
        )
        await self.db.execute(
            update_query,
            (
                hdx_data.get("iso3", None),
                hdx_data.get("hdx_upload", True),
                json.dumps(hdx_data.get("dataset")),
                hdx_data.get("queue", "raw_ondemand"),
                hdx_data.get("meta", False),
                json.dumps(hdx_data.get("categories", {})),
                json.dumps(hdx_data.get("geometry")),
                hdx_id,
            ),
        )
        result = await self.db.fetchone()
        if result:
            return {"update": True}
        raise HTTPException(status_code=404, detail="Item not found")

    async def patch_hdx(self, hdx_id: int, hdx_data: dict):
        """
        Partially update an existing HDX entry in the database.

        Args:
            hdx_id (int): ID of the HDX entry to update.
            hdx_data (dict): Data for partially updating the HDX entry.

        Returns:
            dict: Result of the HDX update process.

        Raises:
            HTTPException: If the HDX entry is not found.
        """
        if not hdx_data:
            raise ValueError("No data provided for update")

        set_clauses = []
        params = []
        for field, value in hdx_data.items():
            set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            if isinstance(value, dict):
                params.append(json.dumps(value))
            else:
                params.append(value)

        query = sql.SQL("UPDATE public.hdx SET {} WHERE id = %s RETURNING *").format(
            sql.SQL(", ").join(set_clauses)