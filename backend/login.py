#! /usr/bin/env python3
# Copyright 2018 Geofabrik GmbH
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
import re
import sys

import requests

CUSTOM_HEADER = {"user-agent": "oauth_cookie_client.py"}


class RaiseError(Exception):
    def __init__(self, message):
        self.message = message


def report_error(message):
    sys.stderr.write("{}\n".format(message))
    raise RaiseError(message)


def find_authenticity_token(response):
    """
    Search the authenticity_token in the response of the server
    """
    pattern = r"name=\"csrf-token\" content=\"([^\"]+)\""
    m = re.search(pattern, response)
    if m is None:
        report_error(
            "Could not find the authenticity_token in the website to be scraped."
        )
    try:
        return m.group(1)
    except IndexError:
        sys.stderr.write(
            "ERROR: The login form does not contain an authenticity_token.\n"
        )
        exit(1)


def verify_me_osm(
    user,
    password,
    osm_host="https://www.openstreetmap.org/",
    consumer_url="https://osm-internal.download.geofabrik.de/get_cookie",
    format="http",
):

    username = user
    if username is None:
        report_error("The username must not be empty.")
    if len(password) == 0 or password is None:
        report_error("The password must not be empty.")
    if consumer_url is None:
        report_error("No consumer URL provided")

    # get request token
    url = consumer_url + "?action=request_token"
    r = requests.post(url, data={}, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error(
            "POST {}, received HTTP status code {} but expected 200".format(
                url, r.status_code
            )
        )
    json_response = json.loads(r.text)
    authorize_url = osm_host + "/oauth/authorize"
    try:
        oauth_token = json_response["oauth_token"]
        oauth_token_secret_encr = json_response["oauth_token_secret_encr"]
    except KeyError:
        report_error("oauth_token was not found in the first response by the consumer")

    # get OSM session
    login_url = osm_host + "/login?cookie_test=true"
    s = requests.Session()
    r = s.get(login_url, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error("GET {}, received HTTP code {}".format(login_url, r.status_code))

    # login
    authenticity_token = find_authenticity_token(r.text)
    login_url = osm_host + "/login"
    r = s.post(
        login_url,
        data={
            "username": username,
            "password": password,
            "referer": "/",
            "commit": "Login",
            "authenticity_token": authenticity_token,
        },
        allow_redirects=False,
        headers=CUSTOM_HEADER,
    )
    if r.status_code != 302:
        report_error(
            "POST {}, received HTTP code {} but expected 302".format(
                login_url, r.status_code
            )
        )

    # authorize
    authorize_url = "{}/oauth/authorize?oauth_token={}".format(osm_host, oauth_token)
    r = s.get(authorize_url, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error(
            "GET {}, received HTTP code {} but expected 200".format(
                authorize_url, r.status_code
            )
        )
    authenticity_token = find_authenticity_token(r.text)

    post_data = {
        "oauth_token": oauth_token,
        "oauth_callback": "",
        "authenticity_token": authenticity_token,
        "allow_read_prefs": [0, 1],
        "commit": "Save changes",
    }
    authorize_url = "{}/oauth/authorize".format(osm_host)
    r = s.post(authorize_url, data=post_data, headers=CUSTOM_HEADER)
    if r.status_code != 200:
        report_error(
            "POST {}, received HTTP code {} but expected 200".format(
                authorize_url, r.status_code
            )
        )

    # logout
    logout_url = "{}/logout".format(osm_host)
    r = s.get(logout_url, headers=CUSTOM_HEADER)
    if r.status_code != 200 and r.status_code != 302:
        report_error(
            "POST {}, received HTTP code {} but expected 200 or 302".format(logout_url)
        )

    # get final cookie
    url = consumer_url + "?action=get_access_token_cookie&format={}".format(format)
    r = requests.post(
        url,
        data={
            "oauth_token": oauth_token,
            "oauth_token_secret_encr": oauth_token_secret_encr,
        },
        headers=CUSTOM_HEADER,
    )

    return str(r.text)
