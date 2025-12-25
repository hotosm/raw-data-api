#!/usr/bin/env python3

# Standard library imports
import argparse
import datetime
import logging
import os
import sys
from enum import Enum

# Third party imports
from dateutil.relativedelta import relativedelta
from psycopg2 import OperationalError, connect
from psycopg2.extras import DictCursor
from tqdm import tqdm

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)


class BatchFrequency(Enum):
    HOURLY = "h"
    DAILY = "d"
    WEEKLY = "w"
    MONTHLY = "m"
    QUARTERLY = "q"
    YEARLY = "y"

    def __str__(self):
        return self.value


def assign_end_date(start, frequency):
    delta_map = {
        BatchFrequency.HOURLY: relativedelta(hours=1),
        BatchFrequency.DAILY: relativedelta(days=1),
        BatchFrequency.WEEKLY: relativedelta(weeks=1),
        BatchFrequency.MONTHLY: relativedelta(months=1),
        BatchFrequency.QUARTERLY: relativedelta(months=3),
        BatchFrequency.YEARLY: relativedelta(years=1),
    }
    return start - delta_map.get(frequency, relativedelta(days=1))


class Database:
    def __init__(self, db_params=None):
        self.db_params = db_params
        self.conn = None
        self.cur = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = (
                connect(**self.db_params)
                if self.db_params
                else connect(
                    host=os.environ["PGHOST"],
                    port=os.environ["PGPORT"],
                    user=os.environ["PGUSER"],
                    password=os.environ["PGPASSWORD"],
                    database=os.environ["PGDATABASE"],
                )
            )
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
            return self.conn, self.cur
        except OperationalError as err:
            self.conn = None
            raise err

    def execute(self, query):
        """Execute SQL query."""
        if not self.conn or not query:
            raise ValueError("Query is null or database is not connected")

        try:
            self.cur.execute(query)
            self.conn.commit()
            try:
                return self.cur.fetchall()
            except:
                return self.cur.statusmessage
        except Exception as err:
            raise err

    def close(self):
        """Close database connection and cursor."""
        if self.conn and self.cur:
            self.cur.close()
            self.conn.close()


class H3Updater:
    def __init__(self):
        self.database = Database()
        self.con, self.cur = self.database.connect()

    def get_timestamp_range(self, table):
        """Get minimum and maximum timestamps from table."""
        query = f'SELECT min("timestamp") as minimum, max("timestamp") as maximum FROM {table};'
        record = self.database.execute(query)
        logging.debug(f"Min: {record[0][0]}, Max: {record[0][1]}")
        return record[0][1], record[0][0]

    def update_h3(self, start, end, table, geom_col, h3_col, resolution, init):
        """Update H3 index for records within date range."""
        init_filter = "" if init else f"AND {h3_col} IS NULL"
        query = f"""
        WITH updated_rows AS (
            SELECT
                osm_id,
                h3_lat_lng_to_cell(ST_Centroid({geom_col}), {resolution}) AS new_h3
            FROM {table}
            WHERE 
                "timestamp" BETWEEN '{start}' AND '{end}'
                {init_filter}
        )
        UPDATE {table} AS t
        SET {h3_col} = u.new_h3
        FROM updated_rows u
        WHERE t.osm_id = u.osm_id;
        """
        self.database.execute(query)

    def batch_update(
        self,
        start_batch_date,
        end_batch_date,
        batch_frequency,
        table,
        geom_col,
        h3_col,
        resolution,
        init=False,
    ):
        """Update H3 index in batches over date range."""
        if start_batch_date is None:
            start_batch_date, _ = self.get_timestamp_range(table)
        if end_batch_date is None:
            _, end_batch_date = self.get_timestamp_range(table)

        if not isinstance(batch_frequency, BatchFrequency):
            raise TypeError("Invalid batch frequency")

        logging.info(
            f"H3 update for {table}.{h3_col} from {start_batch_date} to {end_batch_date}"
        )

        loop_count = self._calculate_loop_count(
            start_batch_date, end_batch_date, batch_frequency
        )
        looping_date = start_batch_date

        with tqdm(total=loop_count, desc=f"Updating {table}:{h3_col}") as pbar:
            while looping_date >= end_batch_date:
                end_date = assign_end_date(looping_date, batch_frequency)
                self.update_h3(
                    start=end_date,
                    end=looping_date,
                    table=table,
                    geom_col=geom_col,
                    h3_col=h3_col,
                    resolution=resolution,
                    init=init,
                )
                pbar.update(1)
                looping_date = end_date

        self.database.close()
        logging.info(f"Finished H3 update for {table}.{h3_col}")

    def _calculate_loop_count(self, start_date, end_date, frequency):
        if frequency in [
            BatchFrequency.WEEKLY,
            BatchFrequency.MONTHLY,
            BatchFrequency.HOURLY,
        ]:
            count = 0
            temp_date = start_date
            while temp_date >= end_date:
                count += 1
                temp_date = assign_end_date(temp_date, frequency)
            return count
        return (start_date - end_date).days


def main():
    parser = argparse.ArgumentParser(
        description="Update H3 column from geometry centroids"
    )
    parser.add_argument(
        "-start",
        "--start",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
        default=None,
        help="Start date for update (default: max timestamp in table)",
    )
    parser.add_argument(
        "-end",
        "--end",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
        default=None,
        help="End date for update (default: min timestamp in table)",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        type=BatchFrequency,
        choices=list(BatchFrequency),
        default=BatchFrequency.DAILY,
        help="Batch frequency (default: DAILY)",
    )
    parser.add_argument(
        "-table",
        "--table",
        default="ways_poly",
        help="Target table name (default: ways_poly)",
    )
    parser.add_argument(
        "-geom",
        "--geom",
        default="geom",
        help="Geometry column name (default: geom)",
    )
    parser.add_argument(
        "-h3",
        "--h3",
        default="h3",
        help="H3 column name to update (default: h3)",
    )
    parser.add_argument(
        "-res",
        "--resolution",
        type=int,
        default=6,
        help="H3 resolution (default: 6)",
    )
    parser.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="Initial setup of the table (default: False)",
    )

    args = parser.parse_args()

    try:
        updater = H3Updater()
        updater.batch_update(
            start_batch_date=args.start,
            end_batch_date=args.end,
            batch_frequency=args.frequency,
            table=args.table,
            geom_col=args.geom,
            h3_col=args.h3,
            resolution=args.resolution,
            init=args.init,
        )
    except Exception as e:
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
