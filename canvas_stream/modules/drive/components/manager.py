from __future__ import print_function
import datetime
from canvas_stream.db.schema import File
from tqdm import tqdm
import json

import requests
from canvas_stream.modules.drive.settings import (
    CREDENTIALS_FILENAME,
    DOWNLOAD_CHUNK_SIZE,
    ROOT_DIR,
    SCOPES,
    TOKENS_DIR,
    TOKENS_FILENAME,
)
from canvas_stream.modules.drive.interfaces.canvas_decorator import CanvasDecorator
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# TODO: Implemented PKCE Worrkflow
# https://www.oauth.com/oauth2-servers/pkce/authorization-code-exchange/
# Create an intermediate webpage to handle secret


class DriveProcessor(CanvasDecorator):
    def __init__(self) -> None:
        self.credentials = None
        self.service = build("drive", "v3", credentials=self.credentials)

    def authenticate(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        token_path = Path(TOKENS_DIR, TOKENS_FILENAME)
        if token_path.exists():
            self.credentials = Credentials.from_authorized_user_file(
                str(token_path), SCOPES
            )
        # If there are no (valid) credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:
            if (
                self.credentials
                and self.credentials.expired
                and self.credentials.refresh_token
            ):
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(Path(ROOT_DIR, CREDENTIALS_FILENAME)), SCOPES
                )

                self.credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with token_path.open("w") as token:
                token.write(self.credentials.to_json())

    def read_files(self):
        # Call the Drive v3 API
        results = (
            self.service.files()
            .list(pageSize=10, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
        else:
            print("Files:")
            for item in items:
                print("{0} ({1})".format(item["name"], item["id"]))

    def _save_file_to_system(self, file: File):
        request_stream: requests.Request = self._api.requester.download(
            file.download_url
        )

        media_body = MediaFileUpload(
            file.name,
            mimetype=request_stream.params["mimeType"],
            resumable=True
        )

        new_file = self.service.files().insert(
            media_body=media_body
        ).execute()

        print(new_file.__dict__)

        resumable_uri = new_file.get("Location")

        filesize = request_stream.headers.get("content-length", None)
        headers = {
            "Content-Range": "bytes 0-" + str(filesize - 1) + "/" + str(filesize)
        }

        if not filesize:
            print(f"???% -- {params['name']}")
            return

        progress = 0
        total_bytes = int(filesize)
        with tqdm(total=total_bytes) as pbar:
            for data in request_stream.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                file_response = requests.put(resumable_uri, headers=headers, data=data)
                progress += len(data)
                pbar.update(len(data))
                print(f"{progress / total_bytes:4.0%} -- {path}", end="\r")

        file.saved_at = datetime.datetime.now().isoformat()
        file.upsert()
