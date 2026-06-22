import json
import os
import tempfile

from forge.core.plugin import Registry


SAMPLE_RECORDS = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "SF"},
]


def _write_test_file(content: str, ext: str) -> str:
    fd, path = tempfile.mkstemp(suffix=f".{ext}")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


class TestCSV:
    def test_roundtrip(self):
        path = _write_test_file("name,age,city\nAlice,30,NYC\nBob,25,SF\n", "csv")
        out = tempfile.mktemp(suffix=".csv")
        reader = Registry.get_reader("csv")()
        records = reader.read(path)
        assert len(records) == 2
        assert records[0]["name"] == "Alice"
        writer = Registry.get_writer("csv")()
        writer.write(records, out)
        with open(out) as f:
            content = f.read()
        assert "Alice" in content
        os.unlink(path)
        os.unlink(out)


class TestJSON:
    def test_roundtrip(self):
        path = _write_test_file(json.dumps(SAMPLE_RECORDS), "json")
        out = tempfile.mktemp(suffix=".json")
        reader = Registry.get_reader("json")()
        records = reader.read(path)
        assert len(records) == 2
        writer = Registry.get_writer("json")()
        writer.write(records, out)
        with open(out) as f:
            data = json.load(f)
        assert len(data) == 2
        os.unlink(path)
        os.unlink(out)
