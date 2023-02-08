#!/usr/bin/env python3
import argparse
import datetime
import os
import subprocess
import sys
import time
from configparser import ConfigParser
from os.path import exists
from urllib.parse import urlparse

import wget


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, help="Data source link or file path")
    parser.add_argument("--host", type=str, help="DB host", default="localhost")
    parser.add_argument("--port", type=str, help="DB port", default="5432")
    parser.add_argument("--user", type=str, help="DB user", default="postgres")
    parser.add_argument("--password", type=str, help="DB password", default="postgres")
    parser.add_argument("--database", type=str, help="DB name", default="postgres")
    parser.add_argument(
        "--include_ref", action="store_true", help="Include ref in output tables"
    )
    parser.add_argument(
        "--replication", action="store_true", help="Prepare tables for replication"
    )
    parser.add_argument(
        "--country",
        type=int,
        help="Fid of the country , if you are loading country , it will filter replication data",
    )
    parser.add_argument(
        "--run_replication",
        action="store_true",
        help="Run replication",
    )
    parser.add_argument(
        "--insert",
        action="store_true",
        help="Run osm2pgsql to insert data , Initial Creation Step",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Run Update on table fields for country continent info",
    )

    parser.add_argument(
        "--download_dir", type=str, help="The directory to download the source file to"
    )

    return parser.parse_args()


def is_local(url):
    url_parsed = urlparse(url)
    if url_parsed.scheme in ("file", ""):  # Possibly a local file
        return exists(url_parsed.path)
    return False


def run_subprocess_cmd(cmd):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.returncode}\nOutput: {e.output.decode()}")
        sys.exit(e.returncode)
    else:
        print(result.stdout.decode())


def run_subprocess_cmd_parallel(cmds):
    procs = [subprocess.Popen(i, env=os.environ) for i in cmds]
    for p in procs:
        p.wait()


if __name__ == "__main__":
    args = parse_arguments()
    os.environ["PGHOST"] = args.host
    os.environ["PGPORT"] = args.port
    os.environ["PGUSER"] = args.user
    os.environ["PGPASSWORD"] = args.password
    os.environ["PGDATABASE"] = args.database

    working_dir = os.path.realpath(os.path.dirname(__file__))
    lua_path = (
        os.path.join(working_dir, "raw_with_ref.lua")
        if args.include_ref
        else os.path.join(working_dir, "raw.lua")
    )
    if not args.source:
        source_path = os.path.join(working_dir, "sample_data/pokhara_all.osm.pbf")
    else:
        source_path = args.source

    if not is_local(source_path):
        download_dir = (
            args.download_dir
            if args.download_dir
            else os.path.join(working_dir, "data")
        )
        if not exists(download_dir):
            os.mkdir(download_dir)

        # Extract the filename from the URL
        filename = os.path.basename(source_path)
        target_path = os.path.join(download_dir, filename)
        if not exists(target_path):
            print(f"Starting download for: {target_path}")
            response = wget.download(source_path, target_path)

        source_path = target_path
    if args.insert:
        osm2pgsql = [
            "osm2pgsql",
            "--create",
            "--slim",
            "--drop" if not args.replication else "",
            "--extra-attributes",
            "--output=flex",
            "--style",
            lua_path,
            source_path,
        ]
        run_subprocess_cmd(osm2pgsql)

        basic_index_cmd = [
            "psql",
            "-a",
            "-f",
            os.path.join(working_dir, "sql/pre_indexes.sql"),
        ]
        run_subprocess_cmd(basic_index_cmd)

        country_table = [
            "psql",
            "-a",
            "-f",
            os.path.join(working_dir, "sql/countries_un.sql"),
        ]
        run_subprocess_cmd(country_table)
    update_cmd_list = []
    if args.update or args.insert:
        print(f"Updating  Nodes:Country Table (5/10) ... \n")
        ## initiate country update for nodes
        field_update_cmd = [
            "python",
            os.path.join(working_dir, "field_update"),
            "-target_table",
            "nodes",
            "--target_column",
            "country",
            "--target_geom",
            "geom",
            "--source_table",
            "countries_un",
            "--source_column",
            "fid",
            "--source_geom",
            "geometry",
            "--type",
            "array",
        ]
        update_cmd_list.append(field_update_cmd)

        ## initiate country update for ways_poly
        field_update_cmd = [
            "python",
            os.path.join(working_dir, "field_update"),
            "--target_table",
            "ways_poly",
            "--target_column",
            "country",
            "--target_geom",
            "geom",
            "--source_table",
            "countries_un",
            "--source_column",
            "fid",
            "--source_geom",
            "geometry",
            "--type",
            "array",
        ]
        update_cmd_list.append(field_update_cmd)
        # grid update for ways_poly
        field_update_cmd = [
            "python",
            os.path.join(working_dir, "field_update"),
            "-target_table",
            "ways_poly",
            "--target_column",
            "continent",
            "--target_geom",
            "geom",
            "--source_table",
            "grid",
            "--source_column",
            "region_id",
            "--source_geom",
            "geometry",
            "--type",
            "int",
        ]
        update_cmd_list.append(field_update_cmd)
