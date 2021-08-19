"Main functions to run the program"

from __future__ import annotations

import datetime
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping
import time

import toml

from .requester import Requester
from .helpers import get_gql_query, html_hyperlink_document, naive_datetime, slugify
from .db_api import DataBase
from . import db as schema
from .db import Course, ExternalURL, File, Folder


StrMapping = Mapping[str, Any]

GQL_COURSES = get_gql_query("courses")
GQL_MODULES_AND_ITEMS = get_gql_query("modules_items")
REST_FAVORITES_COURSES = "/users/self/favorites/courses"


def get_config():
    "Gets the url and access_token from the config file"
    with open("config.toml") as file:
        config = toml.load(file)
    return str(config["url"]), str(config["access_token"])


def main(pause_time=20):
    "Main program. Run Ctrl+Z to stop it"
    print("Starting the program, stop it with Ctrl+Z")
    requester = Requester(*get_config())
    database = DataBase("canvas.db")
    database.load_schema(schema)

    favorite_courses = requester.api_rest(REST_FAVORITES_COURSES)
    for content in favorite_courses:
        course = Course(
            id=content["id"],
            code=content["course_code"],
            name=content["name"],
            is_favorite=True,
        )
        course.upsert()
    database.connection.commit()
    try:
        while True:
            print("Running iteration...")
            _main_loop(requester)
            print(f"Waiting {pause_time} before next iteration")
            time.sleep(pause_time)
    except KeyboardInterrupt:
        sys.exit(0)


def _main_loop(requester: Requester):
    "Main application loop"
    # 1. Check periodically every favorite course to see if it has new content
    courses = requester.api_gql(GQL_COURSES)["allCourses"]
    for content in courses:
        course = next(Course.find(id=content["_id"]), None)

        # The course is not in the list of favorite courses
        if not course:
            continue

        course.updated_at = naive_datetime(content["updatedAt"])
        course.term = content["term"]["name"]
        course.upsert()

        # The course has been already updated
        assert course.updated_at
        if course.saved_at and course.saved_at >= course.updated_at:
            continue

        # 2. Check course modules items (files & external URLs)
        response = requester.api_gql(GQL_MODULES_AND_ITEMS, {"course_id": course.id})
        for module in response["course"]["modulesConnection"]["nodes"]:
            for item in module["moduleItems"]:
                _save_module_item(item, course.id, module)

        # 3. Check folders (files)
        folders = requester.api_rest(f"/courses/{course.id}/folders")
        for folder_info in folders:
            folder = Folder(
                id=folder_info["id"],
                full_name=folder_info["full_name"],
                files_count=folder_info["files_count"],
                course_id=course.id,
                parent_id=folder_info["parent_folder_id"],
                updated_at=naive_datetime(folder_info["updated_at"]),
            )
            # Since checking the files in a folder requieres a request,
            # avoiding making one with the saved_at and updated_at is optimal
            is_saved = folder.saved_at and folder.saved_at >= folder.updated_at
            if folder.files_count == 0 or is_saved:
                continue

            files = requester.api_rest(f"/folders/{folder.id}/files")
            _save_files(files, folder.id, course.id)

            folder.saved_at = datetime.datetime.now().isoformat()
            folder.upsert()

        # 4. Mark the course as saved
        course.saved_at = datetime.datetime.now().isoformat()
        course.upsert()

    # 5. Download the files and links
    for file in File.find_not_saved():
        requester.download(file.download_url, _complete_file_path(file))
        file.saved_at = datetime.datetime.now().isoformat()
        file.upsert()

    # TODO: links (gdown, link file, etc)
    for external_url in ExternalURL.find_not_saved():
        # if external_url is "google drive":
            # gdown.download(external_url.url)

        # Base Case: make a file linking to the URL
        with _complete_external_url_path(external_url).open("w") as io_file:
            io_file.write(html_hyperlink_document(external_url.url))


def _save_module_item(item: StrMapping, course_id: int, module: StrMapping):
    if not item["content"]:
        return

    content = item["content"]
    if content["type"] == "File":
        file = File(
            id=content["_id"],
            course_id=course_id,
            download_url=content["url"],
            name=content["displayName"],
            module_name=module["name"],
            updated_at=naive_datetime(content["updatedAt"]),
        )
        file.upsert()
    elif content["type"] == "ExternalUrl":
        ext_url = ExternalURL(
            id=content["_id"],
            url=content["url"],
            course_id=course_id,
            module_name=module["name"],
            updated_at=naive_datetime(content["updatedAt"]),
            title=content["title"],
        )
        ext_url.upsert()


def _save_files(files: Iterable[StrMapping], folder_id: int, course_id: int):
    for file_data in files:
        file = File(
            id=file_data["id"],
            name=file_data["filename"],
            download_url=file_data["url"],
            updated_at=naive_datetime(file_data["updated_at"]),
            course_id=course_id,
            folder_id=folder_id,
        )
        file.upsert()


def _complete_path(course_id: int, path: Path):
    course = next(Course.find(id=course_id))
    return Path("canvas", slugify(course.name), path)


def _complete_file_path(file: File):
    file_path = Path(slugify(file.name))

    if file.folder_id:
        folder = next(Folder.find(id=file.folder_id))
        parent_path_parts = map(slugify, Path(folder.full_name).parts)
        file_path = Path(*parent_path_parts, file_path)

    return _complete_path(file.course_id, file_path)


def _complete_external_url_path(ext_url: ExternalURL):
    ext_url_path = Path(slugify(ext_url.module_name), slugify(ext_url.title) + ".html")
    return _complete_path(ext_url.course_id, ext_url_path)
