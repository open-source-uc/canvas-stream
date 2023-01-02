"Simple and typed CanvasAPI"

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit
from pathlib import Path
import http.client

import requests

from .helpers import gql_query
from .types import GraphQLCourse, GraphQLModule, RestCourse, RestFile, RestFolder

REQUEST_SCHEME = "https"
REST_ENDPOINT = "/api/v1"
GQL_ENDPOINT = "/api/graphql"
GQL_ALL_COURSES = gql_query("courses")
GQL_MODULES_AND_ITEMS = gql_query("modules_items")


class CanvasAPI:
    "A simple interface for the CanvasAPI"

    def __init__(self, url: str, access_token: str) -> None:
        self._session = requests.session()
        self._location = urlsplit(url).netloc
        self._session.headers.update({"Authorization": f"Bearer {access_token}"})

    def __repr__(self):
        return f"{type(self).__name__}({self._location})"

    def _get(self, url: str, *, stream=False):
        "Makes a GET request to Canvas"
        url_tuple = urlsplit(url)
        if self._location != url_tuple.netloc != "":
            raise ValueError(f"Invalid location for {self}: {url_tuple.netloc}")

        get_url = urlunsplit((REQUEST_SCHEME, self._location, *url_tuple[2:]))
        response = self._session.get(get_url, stream=stream)

        if response.ok:
            return response

        # Handle request error
        code = response.status_code
        mesage = http.client.responses[code]
        raise requests.RequestException(f"Request `{url}` returned: {code} - {mesage}")

    def _rest(self, path: str):
        "REST query that handles pagination"
        response = self._get(f"{REST_ENDPOINT}/{path.strip('/')}")
        new_page = response.links.get("next", None)
        if not new_page:
            return response.json()

        # In this case the response is a json list
        response_data = response.json()
        while new_page:
            pagination_response = self._session.get(new_page["url"])
            response_data.extend(pagination_response.json())
            new_page = response.links.get("next", None)
        return response_data

    def _gql(self, query: str, variables: dict = None) -> dict:
        "Makes a POST request to the GraphQL endpoint"
        # GraphQL pagination is complex, it should be handeled in each GQL method
        url = urlunsplit((REQUEST_SCHEME, self._location, GQL_ENDPOINT, "", ""))
        data = {"query": query, "variables": variables or {}}
        response = self._session.post(url, json=data).json()
        if not "errors" in response:
            return response["data"]

        # GraphQL exceptions should behave like REST exceptions
        errors = ", ".join(map(lambda e: e["message"], response["errors"]))
        raise requests.RequestException(f"GQL error: {errors}")

    def download(self, url: str):
        "Returns a response stream from a `url` that may be used to dowload a file"
        return self._get(url, stream=True)

    def all_courses(self) -> list[GraphQLCourse]:
        "All courses available for the user"
        # This seems to have no pagination
        return self._gql(GQL_ALL_COURSES)["allCourses"]

    def favorite_courses(self) -> list[RestCourse]:
        "Favorite courses (courses displayed in the dashboard)"
        return self._rest("/users/self/favorites/courses")

    def _gql_module(self, course_id: int, after: str = None) -> tuple[dict, list]:
        variables = {"course_id": course_id, "after": after}
        response = self._gql(GQL_MODULES_AND_ITEMS, variables)
        response_data = response["course"]["modulesConnection"]
        return response_data["pageInfo"], response_data["nodes"]

    def modules_with_items(self, course_id: int) -> list[GraphQLModule]:
        "Modules with items (currently only external links and files)"
        page_info, all_modules = self._gql_module(course_id)
        while page_info["hasNextPage"]:
            page_info, modules = self._gql_module(course_id, page_info["endCursor"])
            all_modules.extend(modules)
        return all_modules

    def folders(self, course_id: int) -> list[RestFolder]:
        "Courses folders"
        return self._rest(f"/courses/{course_id}/folders")

    def files(self, folder_id: int) -> list[RestFile]:
        "Files of a folder"
        return self._rest(f"/folders/{folder_id}/files")

    def file(self, file_id: int) -> RestFile:
        "Single file"
        # Fore some reason, GraphQL doesn't generates always the download url
        # It that case, a new request should be made to the REST API
        return self._rest(f"/files/{file_id}")
