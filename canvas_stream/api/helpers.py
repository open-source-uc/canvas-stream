"Helpers"

from pathlib import Path


def gql_query(file_name: str) -> str:
    "Gets a GQL query by it's file name"
    path = Path(__file__).parent.joinpath("gql", file_name).with_suffix(".gql")
    with path.open() as file:
        return file.read()
