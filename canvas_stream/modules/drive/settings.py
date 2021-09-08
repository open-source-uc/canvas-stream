from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
ROOT_DIR = Path(__file__).parents[0]
TOKENS_DIR = Path(ROOT_DIR, "tokens").absolute().resolve()
TOKENS_FILENAME = "token.json"
CREDENTIALS_FILENAME = "credentials.json"
DOWNLOAD_CHUNK_SIZE = 4096
