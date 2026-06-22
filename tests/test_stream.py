import os
import tempfile

from forge.generator.stream import stream_rows, stream_to_csv, stream_to_ndjson, generate_huge


COLUMNS = [
    {"name": "name", "type": "string"},
    {"name": "email", "type": "string"},
    {"name": "age", "type": "integer"},
]


class TestStreamRows:
    def test_streams_correct_count(self):
        rows = list(stream_rows(COLUMNS, count=10))
        assert len(rows) == 10
        assert all("name" in r for r in rows)
        assert all("email" in r for r in rows)

    def test_streams_empty(self):
        rows = list(stream_rows(COLUMNS, count=0))
        assert len(rows) == 0

    def test_streams_with_sample(self):
        sample = [{"name": "Alice", "email": "alice@test.com", "age": 30}]
        rows = list(stream_rows(COLUMNS, count=5, sample=sample))
        assert len(rows) == 5


class TestStreamToCSV:
    def test_writes_csv(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            n = stream_to_csv(COLUMNS, path, count=5, progress=False)
            assert n == 5
            with open(path) as f:
                content = f.read()
            assert "name,email,age" in content
            assert content.count("\n") == 6
        finally:
            os.unlink(path)


class TestStreamToNDJSON:
    def test_writes_ndjson(self):
        fd, path = tempfile.mkstemp(suffix=".ndjson")
        os.close(fd)
        try:
            import json
            n = stream_to_ndjson(COLUMNS, path, count=5, progress=False)
            assert n == 5
            with open(path) as f:
                lines = f.readlines()
            assert len(lines) == 5
            row = json.loads(lines[0])
            assert "name" in row
        finally:
            os.unlink(path)


class TestGenerateHuge:
    def test_generates_by_size(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            n = generate_huge(COLUMNS, path, target_size="1KB", fmt="csv", progress=False)
            assert n > 0
            size = os.path.getsize(path)
            assert size >= 512
        finally:
            os.unlink(path)

    def test_generates_larger_size(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            n = generate_huge(COLUMNS, path, target_size="10KB", fmt="csv", progress=False)
            assert n > 5
            size = os.path.getsize(path)
            assert size >= 5000
        finally:
            os.unlink(path)
