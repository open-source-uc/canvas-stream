"DataBase helpers"

from dataclasses import dataclass
from typing import Optional
from .db_api import Table


@dataclass
class Course(Table):
    id: int
    name: str
    code: str
    term: Optional[str] = None
    is_favorite: Optional[bool] = None
    updated_at: Optional[str] = None
    saved_at: Optional[str] = None


@dataclass
class Folder(Table):
    id: int
    full_name: str
    files_count: int
    course_id: int
    parent_id: int
    updated_at: str
    saved_at: Optional[str] = None


@dataclass
class File(Table):
    id: int
    name: str
    download_url: str
    course_id: int
    folder_id: Optional[int] = None
    updated_at: Optional[str] = None
    saved_at: Optional[str] = None


@dataclass
class ExternalURL(Table):
    id: int
    url: str
    title: str
    course_id: int
    updated_at: Optional[str] = None
    saved_at: Optional[str] = None
