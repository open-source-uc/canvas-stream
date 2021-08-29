from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Any, Callable, Mapping

from requests import Response
from canvas_stream.helpers import slugify
from canvas_stream.db.schema import Course, ExternalURL, File, Folder


HTML_HYPERLINK_DOCUMENT_TEMPLATE = Template(
    "<html><head>"
    '<meta http-equiv="refresh" content="0; url=${url}" />'
    "</head><body>"
    '<a href="{url}">Click here</a>'
    "</body></html>"
)


def html_redirect(external_url: ExternalURL, path: Path):
    "OS-independent solution to make .url like files"
    with path.with_suffix(".html").open("w") as file:
        file.write(HTML_HYPERLINK_DOCUMENT_TEMPLATE.substitute(url=external_url.url))
    return True


def dowload_to_file(request_stream: Response, path: Path, *, chunk_size: int = 4096):
    "Downloads a file"
    content_length = request_stream.headers.get("content-length", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        if not content_length:
            print(f"???% -- {path}")
            file.write(request_stream.content)
            return

        progress = 0
        total_bytes = int(content_length)
        for data in request_stream.iter_content(chunk_size=chunk_size):
            file.write(data)
            progress += len(data)
            print(f"{progress / total_bytes:4.0%} -- {path}", end="\r")
        print(end="\n")


ExternalUrlRecipe = Callable[[ExternalURL, Path], bool]
DowloadFunction = Callable[[str], Response]


class CanvasStreamProvider:
    """
    Canvas Stream provider
    ----------------------
    Functions that handle the program's output.
    It might be subclassed to change it's functionality.
    """

    external_url_download_recipes: list[ExternalUrlRecipe] = [html_redirect]

    def __init__(self, config: Mapping[str, Any], dowload: DowloadFunction) -> None:
        self.config = config
        # Dowloading a file from canvas might requiere credentials.
        # This could be deleted in the future.
        self.dowload = dowload

    def save_file_to_system(self, file: File, path: Path):
        "Dowloads a `file` and saves it to `path`"
        dowload_to_file(self.dowload(file.download_url), path)

    def save_external_url_to_system(self, external_url: ExternalURL, path: Path):
        "Tries each function of `external_url_download_recipes` until one returns `true`"
        for recipe in self.external_url_download_recipes:
            if recipe(external_url, path):
                print(f" URL -- {path}")
                return

    def course_absolute_path(self, course: Course) -> Path:
        """
        Creates an absolute path from the union of the
        configuration value `output_path` and `course.name`.
        """
        return Path(
            self.config.get("output_path", "canvas"), slugify(course.name)
        ).resolve()

    def file_relative_path(self, file: File) -> Path:
        """
        File path relative to its course directory.
        It will the first available betwen the module name
        and the complete folder path as a directory.
        """
        dir_path = Path()
        if file.module_name:
            dir_path = Path(slugify(file.module_name))
        elif file.folder_id:
            folder = next(Folder.find(id=file.folder_id))
            dir_path = Path(*map(slugify, Path(folder.full_name).parts))
        return dir_path.joinpath(slugify(file.name))

    def external_url_relative_path(self, external_url: ExternalURL) -> Path:
        """
        External URL path relative to its course directory.
        It will use the module name as it's directory name and the
        `external_url.title` as it's file name.
        The path will not have a suffix.
        """
        return Path(
            slugify(external_url.module_name), slugify(external_url.title)
        )
