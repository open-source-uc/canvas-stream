"Type annotatins for the CanvasAPI"

from __future__ import annotations
from typing_extensions import TypedDict

Term = TypedDict("Term", {"name": str})


# https://canvas.instructure.com/doc/api/courses.html#method.courses.index
class RestCourse(TypedDict):
    "Rest course"
    course_code: str
    id: int
    name: str


# https://canvas.instructure.com/doc/api/files.html
class RestFile(TypedDict):
    "Rest File"
    filename: str
    id: int
    updated_at: str
    url: str


class RestFolder(TypedDict):
    "Rest Folder"
    files_count: int
    full_name: str
    id: int
    parent_folder_id: int
    updated_at: str


class GraphQLCourse(TypedDict):
    "GraphQL Course item, depends on .gql/courses.gql"
    _id: str
    courseCode: str
    name: str
    state: str
    term: Term
    updatedAt: str


class GraphQLExternalUrlOrFile(TypedDict):
    "GraphQL or external URL, both have the same attribute names"
    _id: str
    name: str
    type: str
    updatedAt: str
    url: str


class GraphQLModuleItem(TypedDict):
    "GraphQL module item (container for the module content)"
    content: GraphQLExternalUrlOrFile
    updatedAt: str


class GraphQLModule(TypedDict):
    "GraphQL course module"
    _id: str
    moduleItems: list[GraphQLModuleItem]
    name: str
    updatedAt: str
