from __future__ import annotations

import os
from typing import Any

from forge.core.plugin import Registry


class Pipeline:
    def __init__(self):
        self.source: str | None = None
        self.source_format: str | None = None
        self.destination: str | None = None
        self.destination_format: str | None = None
        self.mode_name: str | None = None
        self.mode_kwargs: dict[str, Any] | None = None
        self._records: list[dict] = []

    def read(self, source: str, fmt: str | None = None, **kwargs) -> Pipeline:
        self.source = source
        self.source_format = fmt or Registry.detect_format(source)
        if not self.source_format:
            raise ValueError(f"Could not detect format for: {source}")
        reader_cls = Registry.get_reader(self.source_format)
        if not reader_cls:
            raise ValueError(f"No reader for format: {self.source_format}")
        reader = reader_cls()
        self._records = reader.read(source, **kwargs)
        return self

    def apply(self, mode: str, **kwargs) -> Pipeline:
        self.mode_name = mode
        self.mode_kwargs = kwargs
        mode_cls = Registry.get_mode(mode)
        if not mode_cls:
            raise ValueError(f"No mode: {mode}")
        m = mode_cls()
        self._records = m.run(self._records, **kwargs)
        return self

    def write(self, destination: str, fmt: str | None = None, **kwargs) -> Pipeline:
        self.destination = destination
        self.destination_format = fmt or Registry.detect_format(destination)
        if not self.destination_format:
            raise ValueError(f"Could not detect format for: {destination}")
        writer_cls = Registry.get_writer(self.destination_format)
        if not writer_cls:
            raise ValueError(f"No writer for format: {self.destination_format}")
        writer = writer_cls()
        writer.write(self._records, destination, **kwargs)
        return self

    def run(self, **kwargs) -> list[dict]:
        return self._records

    @classmethod
    def go(
        cls,
        source: str,
        destination: str,
        mode: str | None = None,
        source_format: str | None = None,
        dest_format: str | None = None,
        **kwargs,
    ) -> list[dict]:
        pipe = cls()
        pipe.read(source, source_format)
        if mode:
            pipe.apply(mode, **kwargs)
        pipe.write(destination, dest_format)
        return pipe._records
