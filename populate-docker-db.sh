#!/bin/bash
psql -U postgres  raw  < /sql/raw_data.sql
psql -U postgres  underpass < /sql/underpass.sql