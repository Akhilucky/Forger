from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Reader(ABC):
    formats: list[str] = []

    @abstractmethod
    def read(self, source: str, **kwargs) -> list[dict]:
        ...


class Writer(ABC):
    format: str = ""

    @abstractmethod
    def write(self, records: list[dict], destination: str, **kwargs) -> None:
        ...


class Mode(ABC):
    name: str = ""

    @abstractmethod
    def run(self, records: list[dict], **kwargs) -> list[dict]:
        ...


class Registry:
    _readers: dict[str, type[Reader]] = {}
    _writers: dict[str, type[Writer]] = {}
    _modes: dict[str, type[Mode]] = {}

    @classmethod
    def register_reader(cls, reader: type[Reader]) -> type[Reader]:
        for fmt in reader.formats:
            cls._readers[fmt.lower()] = reader
        return reader

    @classmethod
    def register_writer(cls, writer: type[Writer]) -> type[Writer]:
        cls._writers[writer.format.lower()] = writer
        return writer

    @classmethod
    def register_mode(cls, mode: type[Mode]) -> type[Mode]:
        cls._modes[mode.name.lower()] = mode
        return mode

    @classmethod
    def get_reader(cls, fmt: str) -> type[Reader] | None:
        return cls._readers.get(fmt.lower())

    @classmethod
    def get_writer(cls, fmt: str) -> type[Writer] | None:
        return cls._writers.get(fmt.lower())

    @classmethod
    def get_mode(cls, name: str) -> type[Mode] | None:
        return cls._modes.get(name.lower())

    @classmethod
    def list_readers(cls) -> list[str]:
        return list(cls._readers.keys())

    @classmethod
    def list_writers(cls) -> list[str]:
        return list(cls._writers.keys())

    @classmethod
    def list_modes(cls) -> list[str]:
        return list(cls._modes.keys())

    @classmethod
    def detect_format(cls, path: str) -> str | None:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext in cls._readers:
            return ext
        for fmt, reader in cls._readers.items():
            if hasattr(reader, "detect") and reader.detect(path):
                return fmt
        return ext if ext else None
