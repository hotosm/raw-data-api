"""
duckdb.py

Usage : 

async def main():
    async with AsyncDuckDB(db_path="/path/to/database.duckdb") as db:
        await db._run_query_("SELECT * FROM table;")

asyncio.run(main())
"""

# Standard library imports
import asyncio
import os

# Reader imports
import duckdb


class AsyncDuckDB:
    """
    Asynchronous DuckDB class.
    """

    def __init__(self, db_path, temp_dir=None):
        self.db_path = db_path
        self.temp_dir = temp_dir or os.path.join(export_path, "duckdb_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.loop = asyncio.get_event_loop()

    async def __aenter__(self):
        self.con = duckdb.connect(self.db_path)
        dbdict = get_db_connection_params()
        self.db_con_str = convert_dict_to_conn_str(db_dict=dbdict)
        await self.loop.run_in_executor(
            None,
            self.con.sql,
            f"ATTACH '{self.db_con_str}' AS postgres_db (TYPE POSTGRES)",
        )
        await self.loop.run_in_executor(None, self.con.install_extension, "spatial")
        await self.loop.run_in_executor(None, self.con.load_extension, "spatial")
        await self.loop.run_in_executor(
            None,
            self.con.sql,
            f"SET temp_directory = '{os.path.join(self.temp_dir, 'temp.tmp')}'",
        )
        if DUCK_DB_MEMORY_LIMIT:
            await self.loop.run_in_executor(
                None, self.con.sql, f"SET memory_limit = '{DUCK_DB_MEMORY_LIMIT}'"
            )
        if DUCK_DB_THREAD_LIMIT:
            await self.loop.run_in_executor(
                None, self.con.sql, f"SET threads to {DUCK_DB_THREAD_LIMIT}"
            )
        await self.loop.run_in_executor(
            None, self.con.sql, "SET enable_progress_bar = true"
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    async def _run_query_(self, query, attach_pgsql=False, load_spatial=False):
        if attach_pgsql:
            await self.loop.run_in_executor(
                None,
                self.con.sql,
                f"ATTACH '{self.db_con_str}' AS postgres_db (TYPE POSTGRES)",
            )
            load_spatial = True

        if load_spatial:
            await self.loop.run_in_executor(None, self.con.load_extension, "spatial")

        await self.loop.run_in_executor(None, self.con.execute, query)
