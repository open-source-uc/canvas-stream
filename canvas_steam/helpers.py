"Helpers funcitions"

from __future__ import annotations

import unicodedata
import re
from pathlib import Path
from datetime import datetime
from string import Template

import requests


def naive_datetime(dt_str: str):
    "Transfors a datetime string to a naive datetime string"
    return datetime.fromisoformat(dt_str.strip("Z")).replace(tzinfo=None).isoformat()


def get_gql_query(file_name: str) -> str:
    "Gets a GQL query by it's file name"
    path = Path(__file__).parent.joinpath("gql", file_name).with_suffix(".gql")
    with path.open() as file:
        return file.read()


def slugify(value: str) -> str:
    "Makes a string a valid file path"
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .replace(r"/", "-")
        .replace("\\", "-")
        .replace("*", "")
        .replace(":", "")
    )
    return re.sub(r"[-]+", "-", value).strip("_-.")


CHUNK_SIZE = 4096


def dowload_to_file(request_stream: requests.Response, path: Path):
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
        for data in request_stream.iter_content(chunk_size=CHUNK_SIZE):
            file.write(data)
            progress += len(data)
            print(f"{progress / total_bytes:4.0%} -- {path}", end="\r")
        print(end="\n")


HTML_HYPERLINK_DOCUMENT_TEMPLATE = Template(
    """
<html>
    <head>
        <meta http-equiv="refresh" content="0; url=${url}" />
    </head>
</html>
"""
)


def html_hyperlink_document(url: str):
    """OS-independent solution to make .url like files"""
    return HTML_HYPERLINK_DOCUMENT_TEMPLATE.substitute(dict(url=url))
