#!/usr/bin/env bash

if [[ -z "${GALAXY_API_CONFIG_FILE}" ]]; then
    printf "Error: GALAXY_API_CONFIG_FILE environment variable missing.. Exiting!"
    exit 1
fi

echo ${GALAXY_API_CONFIG_FILE} | base64 -d | tee /app/src/config.txt
uvicorn API.main:app --reload --host 0.0.0.0 --port 8000 --log-level error --no-use-colors --proxy-headers
