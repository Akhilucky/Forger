from forge.core.pipeline import Pipeline
from forge.core.plugin import Registry
from forge.core.schema import Schema, DataType, infer_type


class TestSchema:
    def test_infer_from_records(self):
        records = [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False},
        ]
        schema = Schema.infer(records)
        col_map = {c.name: c for c in schema.columns}
        assert col_map["name"].dtype == DataType.STRING
        assert col_map["age"].dtype == DataType.INTEGER
        assert col_map["active"].dtype == DataType.BOOLEAN

    def test_infer_email(self):
        assert infer_type("alice@example.com") == DataType.EMAIL

    def test_infer_uuid(self):
        assert infer_type("550e8400-e29b-41d4-a716-446655440000") == DataType.UUID

    def test_infer_url(self):
        assert infer_type("https://example.com") == DataType.URL


class TestPipeline:
    def test_empty_pipeline(self):
        pipe = Pipeline()
        assert pipe.run() == []


class TestRegistry:
    def test_readers_registered(self):
        assert "csv" in Registry.list_readers()
        assert "json" in Registry.list_readers()

    def test_writers_registered(self):
        assert "csv" in Registry.list_writers()
        assert "json" in Registry.list_writers()

    def test_modes_registered(self):
        for m in ["synthesize", "anonymize", "repair", "convert", "scale", "compress", "enrich", "stress"]:
            assert m in Registry.list_modes(), f"Mode {m} not registered"

    def test_detect_format(self):
        assert Registry.detect_format("data.csv") == "csv"
        assert Registry.detect_format("data.json") == "json"
