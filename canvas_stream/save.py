"Functions to save objects to the database"

from __future__ import annotations

from .db.schema import Course, ExternalURL, File, Folder

from .api.types import (
    GraphQLModule,
    GraphQLModuleItem,
    RestCourse,
    RestFile,
    RestFolder,
)

from .helpers import naive_datetime, userfull_download_url_or_empty_str


def favorite_course(course_data: RestCourse):
    "Saves a favorite course to the database and returns the record"
    course_record = Course(
        id=course_data["id"],
        code=course_data["course_code"],
        name=course_data["name"],
        is_favorite=True,
    )
    course_record.upsert()
    return course_record


def folder(folder_data: RestFolder, course_id: int):
    "Saves a folder to the database and returns the record"
    folder_record = Folder(
        id=folder_data["id"],
        full_name=folder_data["full_name"],
        files_count=folder_data["files_count"],
        course_id=course_id,
        parent_id=folder_data["parent_folder_id"],
        updated_at=naive_datetime(folder_data["updated_at"]),
    )
    folder_record.upsert()
    return folder_record


def module_items(
    items: list[GraphQLModuleItem], course_id: int, module: GraphQLModule
) -> None:
    "Saves a list of module items to the database"
    for item in items:
        if not item["content"]:
            continue

        content = item["content"]
        if content["type"] == "File":
            File(
                id=int(content["_id"]),
                course_id=course_id,
                download_url=userfull_download_url_or_empty_str(content["url"]),
                name=content["name"],
                module_name=module["name"],
                updated_at=naive_datetime(content["updatedAt"]),
            ).upsert()
        elif content["type"] == "ExternalUrl":
            ExternalURL(
                id=int(content["_id"]),
                url=content["url"],
                course_id=course_id,
                module_name=module["name"],
                updated_at=naive_datetime(content["updatedAt"]),
                title=content["name"],
            ).upsert()


def files(files_data: list[RestFile], folder_id: int, course_id: int):
    "Saves a list of files to the database"
    for file_data in files_data:
        File(
            id=file_data["id"],
            name=file_data["filename"],
            download_url=userfull_download_url_or_empty_str(file_data["url"]),
            updated_at=naive_datetime(file_data["updated_at"]),
            course_id=course_id,
            folder_id=folder_id,
        ).upsert()
