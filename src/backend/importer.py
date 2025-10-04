#!/usr/bin/env python3

import argparse
import datetime
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from os.path import exists
from urllib.parse import urlparse

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description="OSM data import using osm2pgsql")
    parser.add_argument("--source", type=str, nargs="+", help="Data source link or file path")

    db_args = [
        ("PGHOST", "--host", "DB host"),
        ("PGPORT", "--port", "DB port"),
        ("PGUSER", "--user", "DB user"),
        ("PGPASSWORD", "--password", "DB password"),
        ("PGDATABASE", "--database", "DB name"),
    ]

    for env, arg, help_text in db_args:
        default = os.getenv(env)
        parser.add_argument(arg, type=str, help=help_text, default=default, required=(not default))

    parser.add_argument("--include_ref", default=False, action="store_true", help="Include ref in output tables")
    parser.add_argument("--fq", type=str, choices=["d", "w", "m", "h"], default="d", help="Field update frequency")
    parser.add_argument("--replication", default=False, action="store_true", help="Prepare tables for replication and runs replication")
    parser.add_argument("--flat_nodes", type=str, help="Flat-nodes option for osm2pgsql")
    parser.add_argument("--cache", type=str, help="Cache size for osm2pgsql")
    parser.add_argument("--country", nargs="+", type=int, help="Country ID for filtering replication data")
    parser.add_argument("--boundary", nargs="+", type=str, help="Boundary geojson for replication filtering")
    parser.add_argument("--skip_cupdate", action="store_true", help="Skip country update during replication")
    parser.add_argument("--insert", action="store_true", help="Run osm2pgsql to insert data")
    parser.add_argument("--update", action="store_true", help="Run update on table fields for country info")
    parser.add_argument("--download_dir", type=str, help="Directory to download source file")
    parser.add_argument("--post_index", default=False, action="store_true", help="Run post index only")
    parser.add_argument("extra_params", nargs="*", metavar="param", help="Extra params to pass to osm2pgsql")

    return parser.parse_args()


def is_local_file(url):
    url_parsed = urlparse(url)
    return url_parsed.scheme in ("file", "") and exists(url_parsed.path)


def run_command(cmd, timeout=None):
    try:
        subprocess.check_output(cmd, env=os.environ, timeout=timeout)
    except subprocess.CalledProcessError as ex:
        print(ex.output)
        raise ex


def run_command_no_fail(cmd, timeout=None):
    try:
        subprocess.check_output(cmd, env=os.environ, timeout=timeout)
    except subprocess.CalledProcessError as ex:
        print(ex.output)


def run_parallel_commands(cmds):
    with Pool(processes=len(cmds)) as pool:
        pool.map(run_command, cmds)


def download_file(download_dir, source_path):
    filename = os.path.basename(source_path)
    target_path = os.path.join(download_dir, filename)
    
    if os.path.exists(target_path):
        return target_path

    print(f"\nDownloading: {source_path}")
    response = requests.get(source_path, stream=True)
    response.raise_for_status()
    
    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded to: {target_path}")
    return target_path


def get_resource_path(relative_path):
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, relative_path)


def run_psql_query(query, dbname="postgres", host=None, port=None, user=None):
    cmd = ["psql", "-h", host, "-p", port, "-U", user, "-d", dbname, "-tAc", query]
    try:
        result = subprocess.check_output(cmd, env=os.environ, stderr=subprocess.DEVNULL)
        return result.decode().strip()
    except subprocess.CalledProcessError:
        return None


def create_database(dbname, host, port, user):
    cmd = ["psql", "-h", host, "-p", port, "-U", user, "-d", "postgres", "-c", f"CREATE DATABASE {dbname};"]
    subprocess.check_output(cmd, env=os.environ, stderr=subprocess.STDOUT)


def enable_extension(extension, dbname, host, port, user, cascade=False):
    cascade_sql = " CASCADE" if cascade else ""
    cmd = ["psql", "-h", host, "-p", port, "-U", user, "-d", dbname, "-c", 
           f"CREATE EXTENSION IF NOT EXISTS {extension}{cascade_sql};"]
    subprocess.check_output(cmd, env=os.environ, stderr=subprocess.STDOUT)


def setup_database_prerequisites(dbname, host, port, user):
    if run_psql_query(f"SELECT 1 FROM pg_database WHERE datname='{dbname}'", "postgres", host, port, user) != "1":
        print(f"Creating database: {dbname}")
        try:
            create_database(dbname, host, port, user)
        except subprocess.CalledProcessError as e:
            print(f"Failed to create database: {e.output.decode()}")
            sys.exit(1)
    
    required_extensions = [("postgis", False), ("h3", False), ("h3_postgis", True)]
    missing = [ext for ext, _ in required_extensions if 
               run_psql_query(f"SELECT 1 FROM pg_available_extensions WHERE name='{ext}'", "postgres", host, port, user) != "1"]
    
    if missing:
        print(f"Missing extensions: {', '.join(missing)}")
        print("Install with: sudo apt install postgresql-16-postgis-3 postgresql-16-h3")
        sys.exit(1)
    
    for ext, cascade in required_extensions:
        if run_psql_query(f"SELECT 1 FROM pg_extension WHERE extname='{ext}'", dbname, host, port, user) != "1":
            try:
                enable_extension(ext, dbname, host, port, user, cascade)
            except subprocess.CalledProcessError as e:
                print(f"Failed to enable extension {ext}: {e.output.decode()}")
                sys.exit(1)


def main():
    args = parse_arguments()

    os.environ["PGHOST"] = args.host
    os.environ["PGPORT"] = args.port
    os.environ["PGUSER"] = args.user
    os.environ["PGPASSWORD"] = args.password
    os.environ["PGDATABASE"] = args.database

    start_time = time.time()

    lua_file = "raw_with_ref.lua" if args.include_ref else "raw.lua"
    lua_path = get_resource_path(f"lua/{lua_file}")

    source_paths = args.source or [get_resource_path("sample_data/pokhara_all.osm.pbf")]
    download_dir = args.download_dir or get_resource_path("data")
    
    os.makedirs(download_dir, exist_ok=True)

    target_paths = [
        download_file(download_dir, src) if not os.path.isfile(src) else src
        for src in source_paths
    ]

    if len(target_paths) > 1:
        merged_path = os.path.join(download_dir, "merged_data.pbf")
        if not os.path.exists(merged_path):
            print(f"\nMerging OSM files: {target_paths}")
            subprocess.run(["osmium", "merge", *target_paths, "-o", merged_path], check=True)
        source_path = merged_path
    else:
        source_path = target_paths[0]

    if args.insert:
        setup_database_prerequisites(args.database, args.host, args.port, args.user)
        
        osm2pgsql_cmd = [
            "osm2pgsql",
            "--create",
            "--slim",
            "--extra-attributes",
            "--output=flex",
            "--style", lua_path,
        ]

        if not args.replication:
            osm2pgsql_cmd.append("--drop")

        if args.flat_nodes:
            osm2pgsql_cmd.extend(["--flat-nodes", args.flat_nodes])

        if args.cache:
            osm2pgsql_cmd.extend(["--cache", str(args.cache)])

        if args.extra_params:
            osm2pgsql_cmd.extend(args.extra_params)

        osm2pgsql_cmd.append(source_path)

        print(f"Running: {' '.join(osm2pgsql_cmd)}")
        run_command(osm2pgsql_cmd)

        run_command(["psql", "-a", "-f", get_resource_path("sql/pre_indexes.sql")])
        run_command(["psql", "-a", "-f", get_resource_path("sql/countries.sql")])

        if args.replication:
            run_command(["python", get_resource_path("replication"), "init"])

    update_cmds = []
    if args.update or args.insert:
        if not args.skip_cupdate:
            for table in ["nodes", "ways_poly", "ways_line", "relations"]:
                cmd = [
                    "raw-field-update",
                    "-table", table,
                    "--h3", "h3",
                    "--res", "6",
                    "--f", args.fq,
                ]
                update_cmds.append(cmd)

    if len(update_cmds) > 1:
        run_parallel_commands(update_cmds)

    if args.insert:
        run_command(["psql", "-a", "-f", get_resource_path("sql/users.sql")])
        print("Users table created")

    if args.insert or args.post_index:
        run_command(["psql", "-a", "-f", get_resource_path("sql/post_indexes.sql")])
        elapsed = datetime.timedelta(seconds=(time.time() - start_time))
        print(f"\nProcess finished. Total time: {elapsed}")

    if args.replication:
        print("Starting replication")
        replication_cmd = [
            "python", get_resource_path("replication"),
            "update",
            "-s", "raw.lua",
            "--max-diff-size", "10",
            "--once",
        ]

        if args.flat_nodes:
            replication_cmd.extend(["--flat_nodes", args.flat_nodes])

        if args.country:
            replication_cmd.extend(["--country"] + [str(x) for x in args.country])

        if args.boundary:
            replication_cmd.extend(["--boundary"] + args.boundary)

        if args.skip_cupdate:
            replication_cmd.append("--skip_cupdate")

        run_command(replication_cmd)


if __name__ == "__main__":
    main()
