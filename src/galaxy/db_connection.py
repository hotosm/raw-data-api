# Copyright (C) 2021 Humanitarian OpenStreetmap Team

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>

from .config import config
import logging
import psycopg2
from psycopg2 import pool
from .config import get_db_connection_params


class Database:
    """Handles the all work related to connection pooling
    """
    def __init__(self):
        self.db_params = get_db_connection_params("RAW_DATA")
        self._cursor = None
        self.threaded_postgreSQL_pool  = None
        self.con = None

    def connect(self):
        """Connection to the database 
        """
        if not self.threaded_postgreSQL_pool :
            try:
                #creating pool through psycopg2 with threaded connection so that there will support minimum 5 users to 20 users 
                self.threaded_postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(3, 20,**self.db_params)
                logging.debug("Connection pooling has been established")
                if (self.threaded_postgreSQL_pool):
                    logging.debug("Connection pool created successfully using ThreadedConnectionPool")
            except Exception as e:
                logging.error(e)
    
    def get_conn_from_pool(self):
        """Function to get connection from the pool instead of new connection

        Returns:
            connection 
        """
        if (self.threaded_postgreSQL_pool):
            # Use getconn() method to Get Connection from connection pool
            pool_conn = self.threaded_postgreSQL_pool.getconn()
            return pool_conn

    def release_conn_from_pool(self,pool_con):
        """Can be used to release specific connection after its use from the pool , so that it can be used by another process

        Args:
            pool_con (_type_): define which connection to remove from pool

        Raises:
            ex: error if connection doesnot exists or misbehave of function
        """
        try:
            # Use this method to release the connection object and send back ti connection pool
            self.threaded_postgreSQL_pool.putconn(pool_con)
            logging.debug("Putting back postgresql connection to thread")
        except :
            logging.debug("Connection doesn't exist in Pool")
    
    async def close_all_connection_pool(self):
        """Closes the connection thread created by thread pooling all at once 
        """
        # closing database connection.
        # use closeall() method to close all the active connection if you want to turn of the application
        if self.threaded_postgreSQL_pool:
            await self.threaded_postgreSQL_pool.closeall
        logging.debug("Threaded PostgreSQL connection pool is closed")

