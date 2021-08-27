"DB helper API"

# This "DB API" is a simplified version of an experiment that I have been doing
# with a toy ORM. Some things are hardcoded for simplicity, like the pk.

# Note: a new python module has been recently released, with the same interface
# to create tables, https://github.com/tiangolo/sqlmodel.

from __future__ import annotations
import sqlite3
from typing import Any, DefaultDict, Iterator, Type, TypeVar
from collections import defaultdict


T = TypeVar("T", bound="Table")

PYTHON_TO_SQLITE: DefaultDict[type | None, str] = defaultdict(
    lambda: "TEXT",
    {
        None: "NULL",
        float: "REAL",
        int: "INTEGER",
        bool: "INTEGER",
    },
)


def is_table(obj):
    "Checks if an object or a type is a subclass of Table"
    return isinstance(obj, type) and issubclass(obj, Table) and obj is not Table


class MetaTable(type):
    "MetaClass for the Table class"

    def __init_subclass__(cls) -> None:
        assert "id" in cls.__annotations__
        return super().__init_subclass__()

    def __repr__(cls: type):
        db_name = getattr(cls, "__db__", "")
        name = f"{f'{db_name}.' if db_name else ''}{cls.__name__}"
        annotations = cls.__dict__.get("__annotations__", {})
        attrs = (f"{a}:{t.__name__}" for a, t in annotations.items())
        return f"<Table {name}({', '.join(attrs)})>"


class Table(metaclass=MetaTable):
    "DB table helper"
    __db__: DataBase
    __annotations__: dict[str, type]

    def upsert(self):
        """SQl upset statement. Used to update not null values."""
        data = self.__dict__
        values_to_update = (f"{k}=:{k}" for k, v in data.items() if v)
        statement = (
            f"INSERT INTO {type(self).__name__}"
            f" VALUES ({', '.join(f':{k}' for k in data)})"
            f" ON CONFLICT (id) DO UPDATE SET {', '.join(values_to_update)}"
        )
        self.__db__.connection.cursor().execute(statement, data)
        self.__db__.connection.commit()

    @classmethod
    def create_table(cls):
        "Creates the table"
        attrs = [f"{n} {PYTHON_TO_SQLITE[t]}" for n, t in cls.__annotations__.items()]
        params = [*attrs, "PRIMARY KEY (id)"]
        statement = f"CREATE TABLE IF NOT EXISTS {cls.__name__} ({', '.join(params)})"
        cls.__db__.connection.cursor().execute(statement)

    @classmethod
    def find(cls: Type[T], **eq: Any) -> Iterator[T]:
        "SQL find statement"
        statement = (
            f"SELECT {', '.join(cls.__annotations__)} FROM {cls.__name__}"
            f"{(' WHERE ' + 'AND '.join(f'{k}=:{k}' for k in eq)) if eq else ''}"
        )
        cursor = cls.__db__.connection.cursor()
        return ResultIterator(cls, cursor.execute(statement, eq))

    @classmethod
    def find_not_saved(cls: Type[T]) -> Iterator[T]:
        "Find not saved items"
        assert "updated_at" in cls.__annotations__
        assert "saved_at" in cls.__annotations__
        statement = (
            f"SELECT {', '.join(cls.__annotations__)} FROM {cls.__name__}"
            f" WHERE (updated_at > saved_at) OR (saved_at IS NULL)"
        )
        return ResultIterator(cls, cls.__db__.connection.cursor().execute(statement))


class ResultIterator:
    def __init__(self, cls: type, cursor: sqlite3.Cursor) -> None:
        self._class = cls
        self._cursor = cursor

    def __iter__(self):
        return self

    def __next__(self):
        result = self._cursor.fetchone()
        if not result:
            raise StopIteration
        return self._class(*result)


class DataBase:
    "Database helper"

    def __init__(self, database: str):
        self.connection = sqlite3.connect(database)
        self.tables: list[Table] = []

    def load_schema(self, schema_module):
        "Load a module schema"
        for object_name in dir(schema_module):
            m_obj = getattr(schema_module, object_name)
            if is_table(m_obj):
                setattr(m_obj, "__db__", self)
                self.tables.append(m_obj)
        for table in self.tables:
            table.create_table()
