"""
postgres.py

This module provides an asynchronous PostgreSQL connection class, `AsyncPostgres`, which can be used to establish a connection pool, execute queries, and manage transactions.

Usage:
1. Import the `AsyncPostgres` class:
    from postgres import AsyncPostgres

2. Create an instance of the `AsyncPostgres` class with your database URL:
    db = AsyncPostgres('postgresql://user:password@host:port/database')

3. Establish a connection pool:
    await db.establish_pool()

4. Execute queries using the provided methods:
    await db.execute("INSERT INTO table (column1, column2) VALUES ($1, $2)", value1, value2)
    rows = await db.fetch("SELECT * FROM table")
    row = await db.fetchrow("SELECT * FROM table WHERE id=$1", row_id)
    value = await db.fetchval("SELECT count(*) FROM table")

5. Manage transactions:
    tx = await db.start_transaction()
    await db.execute("INSERT INTO table ...", *args, transaction=tx)
    await db.commit_transaction(tx)

6. Close the connection pool when you're done:
    await db.close_pool()

"""

# Third party imports
import asyncpg


class AsyncPostgres:
    """Asynchronous PostgreSQL connection class, `AsyncPostgres`, which can be used to establish a connection pool, execute queries, and manage transactions."""

    def __init__(self, database_url):
        """
        Initialize the AsyncPostgres class with the provided database URL.

        Args:
            database_url (str): The URL for the PostgreSQL database.
        """
        self._database_url = database_url
        self._pool = None

    async def establish_pool(self):
        """
        Establish a connection pool for the PostgreSQL database.

        Example:
            await db.establish_pool()
        """
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._database_url)

    async def close_pool(self):
        """
        Close the connection pool for the PostgreSQL database.

        Example:
            await db.close_pool()
        """
        if self._pool is not None:
            await self._pool.close()

    async def execute(self, query, *args, timeout=None):
        """
        Execute a SQL query on the PostgreSQL database.

        Args:
            query (str): The SQL query to execute.
            *args: Positional arguments to be passed to the query.
            timeout (Optional[float]): The maximum time to wait for the query to complete (in seconds).

        Returns:
            str: The status of the query execution.

        Example:
            await db.execute("INSERT INTO table (column1, column2) VALUES ($1, $2)", value1, value2)
        """
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(self, query, *args, timeout=None):
        """
        Fetch rows from the PostgreSQL database based on the provided SQL query.

        Args:
            query (str): The SQL query to execute.
            *args: Positional arguments to be passed to the query.
            timeout (Optional[float]): The maximum time to wait for the query to complete (in seconds).

        Returns:
            list: A list of rows fetched from the database.

        Example:
            rows = await db.fetch("SELECT * FROM table")
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(self, query, *args, timeout=None):
        """
        Fetch a single row from the PostgreSQL database based on the provided SQL query.

        Args:
            query (str): The SQL query to execute.
            *args: Positional arguments to be passed to the query.
            timeout (Optional[float]): The maximum time to wait for the query to complete (in seconds).

        Returns:
            asyncpg.Record: A single row fetched from the database.

        Example:
            row = await db.fetchrow("SELECT * FROM table WHERE id=$1", row_id)
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    async def fetchval(self, query, *args, timeout=None):
        """
        Fetch a single value from the PostgreSQL database based on the provided SQL query.

        Args:
            query (str): The SQL query to execute.
            *args: Positional arguments to be passed to the query.
            timeout (Optional[float]): The maximum time to wait for the query to complete (in seconds).

        Returns:
            Any: The fetched value from the database.

        Example:
            value = await db.fetchval("SELECT count(*) FROM table")
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)

    async def fetch_chunks(self, query, *args, chunk_size=1000, timeout=None):
        """
        Fetch rows from the PostgreSQL database in chunks using a server-side cursor.

        Args:
            query (str): The SQL query to execute.
            *args: Positional arguments to be passed to the query.
            chunk_size (int): The number of rows to fetch in each chunk.
            timeout (Optional[float]): The maximum time to wait for the query to complete (in seconds).

        Yields:
            list: A list of rows fetched from the database.

        Example:
            async for chunk in db.fetch_chunks("SELECT * FROM large_table", chunk_size=5000):
                process_chunk(chunk)
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                async with conn.cursor(
                    f"fetch_chunks_{chunk_size}", prefetch=chunk_size
                ) as cursor:
                    await cursor.execute(query, *args, timeout=timeout)
                    while True:
                        chunk = await cursor.fetch(chunk_size)
                        if not chunk:
                            break
                        yield chunk

    async def start_transaction(self):
        """
        Start a transaction on the PostgreSQL database.

        Returns:
            asyncpg.Transaction: The transaction object.

        Example:
            tx = await db.start_transaction()
        """
        async with self._pool.acquire() as conn:
            tx = conn.transaction()
            await tx.start()
            return tx

    async def commit_transaction(self, tx):
        """
        Commit a transaction on the PostgreSQL database.

        Args:
            tx (asyncpg.Transaction): The transaction object.

        Example:
            await db.commit_transaction(tx)
        """
        await tx.commit()

    async def rollback_transaction(self, tx):
        """
        Rollback a transaction on the PostgreSQL database.

        Args:
            tx (asyncpg.Transaction): The transaction object.

        Example:
            await db.rollback_transaction(tx)
        """
        await tx.rollback()
