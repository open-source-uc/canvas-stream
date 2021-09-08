from abc import ABCMeta, abstractmethod
from typing import Any


class Stream(metaclass=ABCMeta):
    @abstractmethod
    def _save_file_to_system(self):
        pass


class CanvasDecorator(Stream):
    def __init__(self, api):
        self._api = api

    @abstractmethod
    def _save_file_to_system(self):
        pass

    def __getattr__(self, name: str):
        return getattr(self._api, name)
