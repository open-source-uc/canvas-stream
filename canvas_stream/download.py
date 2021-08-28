"Helpers to download files"

from pathlib import Path

import requests

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
