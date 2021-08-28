"Main functions to run the program"

from __future__ import annotations

import datetime
from pathlib import Path
import sys
import time

import toml
from requests import RequestException

from .api import CanvasAPI

from .helpers import (
    html_hyperlink_document,
    naive_datetime,
    slugify,
    userfull_download_url_or_empty_str,
)
from .download import dowload_to_file

from .db import DataBase, schema
from .db.schema import Course, ExternalURL, File, Folder

from . import save


def main(pause_time=60, iterate=True):
    "Runs `CanvasStream().run()`"
    CanvasStream().run(pause_time, iterate)

class CanvasStream:
    def __init__(self) -> None:
        with open("config.toml") as file:
            self.config = toml.load(file)
        self.database = DataBase(self.config.get("db_name", "canvas.db"))
        self.database.load_schema(schema)
        self.requester = CanvasAPI(
            url=self.config["url"],
            access_token=self.config["access_token"]
        )

    def run(self, pause_time=60, iterate=True):
        "Main program. Run Ctrl+Z to stop it"
        print("Starting the program, stop it with Ctrl+Z")
        for course in self.requester.favorite_courses():
            save.favorite_course(course)
        if not iterate:
            self._run_iteration()
            return
        try:
            while True:
                print("Running iteration...")
                self._run_iteration()
                print(f"Waiting {pause_time} seconds before next iteration")
                time.sleep(pause_time)
        except KeyboardInterrupt:
            sys.exit(0)

    def _run_iteration(self):
        "Main application loop"
        courses = self.requester.all_courses()
        for content in courses:
            course = next(Course.find(id=content["_id"]), None)

            # The course is not in the list of favorite courses
            if not course:
                continue

            course.updated_at = naive_datetime(content["updatedAt"])
            course.term = content["term"]["name"]
            course.upsert()

            # See if the course hasn't been saved or has been updated
            if not course.saved_at or course.saved_at < course.updated_at:
                print(f"Updating references of {course.name}")
                self._update_courses_references(course)

        print("Dowloading new files...")
        for file in File.find_not_saved():
            self._save_file_to_system(file)

        for external_url in ExternalURL.find_not_saved():
            self._save_external_url_to_system(external_url)

    def _update_courses_references(self, course: Course):
        # Check course modules items (files & external URLs)
        modules = self.requester.modules_with_items(course.id)
        for module in modules:
            save.module_items(module["moduleItems"], course.id, module)

        # Check folders (files)
        folders = self.requester.folders(course.id)
        for folder_info in folders:
            folder = save.folder(folder_info, course.id)
            # Since checking the files in a folder requieres a request,
            # avoiding making one with the saved_at and updated_at is optimal
            is_saved = folder.saved_at and folder.saved_at >= folder.updated_at
            if folder.files_count == 0 or is_saved:
                continue

            try:
                files = self.requester.files(folder.id)
                save.files(files, folder.id, course.id)
                folder.saved_at = datetime.datetime.now().isoformat()
                folder.upsert()
            except RequestException:
                print(f"Request error with folder {folder.id} ({course.name})")

        # Mark the course as saved
        course.saved_at = datetime.datetime.now().isoformat()
        course.upsert()

    def _save_file_to_system(self, file: File):
        # In some cases, the URL obtained from the API
        # doesn't have the verifier that makes it posible
        # to download the file.
        # `download_url` will be empty in those cases.
        if not file.download_url:
            # A now request is made here to try again, but now
            # only asking for the information of the file
            file_data = self.requester.file(file.id)
            file.download_url = userfull_download_url_or_empty_str(file_data["url"])
            if not file.download_url:
                return

        dowload_to_file(self.requester.download(file.download_url), self._complete_file_path(file))

        file.saved_at = datetime.datetime.now().isoformat()
        file.upsert()

    def _save_external_url_to_system(self, external_url: ExternalURL):
        # if external_url is "google drive":
        # gdown.download(external_url.url)

        # Base Case: make a file linking to the URL
        external_url_path = self._complete_external_url_path(external_url)
        external_url_path.parent.mkdir(parents=True, exist_ok=True)
        print(f" URL -- {external_url_path}")
        with external_url_path.open("w") as io_file:
            io_file.write(html_hyperlink_document(external_url.url))
        external_url.saved_at = datetime.datetime.now().isoformat()
        external_url.upsert()

    def _complete_path(self, course_id: int, path: Path) -> Path:
        course = next(Course.find(id=course_id))
        return Path(self.config.get("output_path", "canvas"), slugify(course.name), path)

    def _complete_file_path(self, file: File) -> Path:
        file_path = Path(slugify(file.name))

        if file.folder_id:
            folder = next(Folder.find(id=file.folder_id))
            parent_path_parts = map(slugify, Path(folder.full_name).parts)
            file_path = Path(*parent_path_parts, file_path)

        return self._complete_path(file.course_id, file_path)

    def _complete_external_url_path(self, ext_url: ExternalURL) -> Path:
        ext_url_path = Path(slugify(ext_url.module_name), slugify(ext_url.title) + ".html")
        return self._complete_path(ext_url.course_id, ext_url_path)
