# Adding a custom provider

A _provider_ class (subclasses of `CanvasStreamProvider`) is a class
of objects that provide key functionalities to tha main loop of the
program, but aren't related to the main loop logic.

This follows the [strategy][1] (or [provider][2]) pattern, witch allows
customization to actions like downloading a file or naming a directory.

In short, the API works as follows:

```python
from canvas_stream import CanvasStream, CanvasStreamProvider

# a download external url recipe that returns true if the
# external url could be saved to the system, false otherwise
def custom_recipe(external_url, path) -> bool: ...

class CustomProvider(CanvasStreamProvider):
    # Everything below is optional
    # A CanvasStreamProvider will have the attribute
    # `config`, the configuration options given to CanvasStream
    external_url_download_recipes = [
        custom_recipe,
        *CanvasStreamProvider.external_url_download_recipes
    ]
    def save_file_to_system(self, file, path) -> None: ...
    def save_external_url_to_system(self, external_url, path) -> None: ...
    def course_relative_path(self, course) -> Path: ...
    def file_relative_path(self) -> Path: ...
    def external_url_relative_path(self, external_url) -> Path: ...

canvas_stream_instance = CanvasStream()
canvas_stream_instance.set_provider(CustomProvider)
canvas_stream_instance.run()
```

The code should be invoked from the file with that code, not the
module itself. For example, if the file is named `./code.py`,
the program should be invoked like `python code.py`,
not `python -m canvas_stream`.


## Complete example

```py
# ./run.py

from __future__ import annotations

import re
from typing import TYPE_CHECKING

# External dependency
import gdown

# You should only import from `canvas_stream` and `canvas_stream.helpers`
from canvas_stream import CanvasStream, CanvasStreamProvider
from canvas_stream.helpers import slugify

# This will obtain the types used for type checking, the code
# inside will not be evaluated (`TYPE_CHECKING` will be False at runtime)
if TYPE_CHECKING:
    from pathlib import Path
    from canvas_stream.db.schema import Course, ExternalURL


# Recipe for downloading an external URL,
# that catches URLs that are from Google Drive
def download_from_google_drive(external_url: ExternalURL, path: Path) -> bool:
    "Downloads a file from google drive if the url is from drive"
    #! this is an example: it will fail with non-public files
    match = re.search(r"drive\.google\.com/file/d/(?P<id>[^/]*?)/", external_url.url)
    if match:
        print("Downloading from Google Drive")
        download_url = f"https://drive.google.com/uc?id={match.group('id')}"
        gdown.download(url=download_url, output=str(path))
        return True
    return False


class CustomProvider(CanvasStreamProvider):
    "Custom provider that downloads files from google drive"
    external_url_download_recipes = [
        # Include custom recipes
        download_from_google_drive,
        # Include the default recipes
        *CanvasStreamProvider.external_url_download_recipes
    ]
    def course_relative_path(self, course: Course) -> Path:
        # changes the course directory name
        return Path(slugify(course.code))


canvas_stream_instance = CanvasStream()
canvas_stream_instance.set_provider(CustomProvider)
canvas_stream_instance.run()
```

[1]: https://en.wikipedia.org/wiki/Strategy_pattern
[2]: https://en.wikipedia.org/wiki/Provider_model

