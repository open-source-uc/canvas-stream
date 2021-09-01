"Helpers funcitions"

from __future__ import annotations

import unicodedata
import re
from datetime import datetime
from string import Template
from urllib.parse import urlsplit, parse_qs


def naive_datetime(dt_str: str):
    "Transfors a datetime string to a naive datetime string"
    return datetime.fromisoformat(dt_str.strip("Z")).replace(tzinfo=None).isoformat()


def slugify(value: str) -> str:
    "Makes a string a valid file path"
    # TODO: find a better way to do this
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .replace(r"/", "-")
        .replace("\\", "-")
        .replace("*", "")
        .replace(":", "")
        .replace("?", "")
        .replace("|", "")
    )
    return re.sub(r"[-]+", "-", value).strip("_-. ")


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
    return HTML_HYPERLINK_DOCUMENT_TEMPLATE.substitute({"url": url})


def userfull_download_url_or_empty_str(url: str):
    "Verifies if the `verifier` key is in the url parameters"

    if "verifier" in parse_qs(urlsplit(url).query):
        return url
    return ""
