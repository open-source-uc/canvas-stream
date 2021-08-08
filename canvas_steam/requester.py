"Utils to handle requests"

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit, parse_qs
from pathlib import Path
import http.client

import requests

from .helpers import dowload_to_file

REQUEST_SCHEME = "https"
ADDITIONAL_HEADERS = {"per_page": "50"}
REST_ENDPOINT = "/api/v1"
GQL_ENDPOINT = "/api/graphql"


class Requester:
    "Canvas Request Wrapper"

    def __init__(self, url: str, access_token: str):
        self.location = urlsplit(url).netloc
        self.access_token = access_token
        self.request_headers = {
            "Authorization": f"Bearer {access_token}",
            **ADDITIONAL_HEADERS,
        }

    def __repr__(self):
        return f"CanvasRequester({self.location})"

    def get(self, url: str, *, stream=False):
        "Makes a GET request to Canvas"
        url_tuple = urlsplit(url)
        if self.location != url_tuple.netloc != "":
            raise ValueError(f"Invalid location for {self}: {url_tuple.netloc}")

        get_url = urlunsplit((REQUEST_SCHEME, self.location, *url_tuple[2:]))
        response = requests.get(get_url, headers=self.request_headers, stream=stream)

        if response.ok:
            return response

        code = response.status_code
        mesage = http.client.responses[code]
        raise requests.RequestException(f"Request `{url}` returned: {code} - {mesage}")

    def api_gql(self, query: str, variables: dict = None):
        "Makes a POST request to the GQL endpoint"
        url = urlunsplit((REQUEST_SCHEME, self.location, GQL_ENDPOINT, "", ""))
        data = {"query": query, "variables": variables or {}}
        response = requests.post(url, json=data, headers=self.request_headers).json()
        if not "errors" in response:
            return response["data"]
        errors = ", ".join(map(lambda e: e["message"], response["errors"]))
        raise requests.RequestException(f"GQL error: {errors}")

    def api_rest(self, path: str):
        "Mages a GET request to the Canvas API"
        return self.get(f"{REST_ENDPOINT}/{path.strip('/')}").json()

    def download(self, url: str, path: Path):
        "Downloads a file from a Canvas `url` to a `path`"
        # TODO: this check should be donde when saving the url to the database
        if "verifier" not in parse_qs(urlsplit(url).query):
            print(f"Error: skiping file: {path}")
        else:
            dowload_to_file(self.get(url, stream=True), path)
