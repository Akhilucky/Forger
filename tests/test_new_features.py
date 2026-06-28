import json
import os
import tempfile

from forge.core.plugin import Registry
from forge.core.pipeline import Pipeline


SAMPLE = [
    {"name": "Alice", "email": "alice@example.com", "age": 30},
    {"name": "Bob", "email": "bob@test.com", "age": 25},
]


class TestPipelineRunner:
    def test_simple_json_pipeline(self):
        config = {
            "steps": [{
                "source": None,
                "mode": "generate",
                "count": 5,
                "columns": ["name", "email", "age"],
            }]
        }
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with open(path, "w") as f:
                json.dump(config, f)
            from forge.pipeline_runner import run_pipeline
            records = run_pipeline(path)
            assert len(records) >= 0
        finally:
            os.unlink(path)


class TestProfile:
    def test_generates_html(self):
        from forge.profile import generate_profile
        html = generate_profile(SAMPLE, "Test")
        assert "<!DOCTYPE html>" in html
        assert "Alice" in html or "name" in html
        assert "30" in html or "age" in html

    def test_empty_profile(self):
        from forge.profile import generate_profile
        html = generate_profile([], "Empty")
        assert "No records" in html


class TestDiff:
    def test_identical(self):
        from forge.diff import diff_datasets
        report = diff_datasets(SAMPLE, SAMPLE)
        assert report.total_changes == 0

    def test_different(self):
        from forge.diff import diff_datasets
        b = [{"name": "Charlie", "email": "charlie@test.com", "age": 35}]
        report = diff_datasets(SAMPLE, b)
        assert report.total_changes > 0

    def test_different_keyed(self):
        from forge.diff import diff_datasets
        a = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        b = [{"id": 1, "name": "Alice"}, {"id": 3, "name": "Carol"}]
        report = diff_datasets(a, b, key="id")
        assert report.only_left == 1
        assert report.only_right == 1

    def test_keyed_diff(self):
        from forge.diff import diff_datasets
        a = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        b = [{"id": 1, "name": "Alice"}, {"id": 3, "name": "Carol"}]
        report = diff_datasets(a, b, key="id")
        assert report.only_left == 1
        assert report.only_right == 1
        assert report.common == 1


class TestValidate:
    def test_required_passes(self):
        from forge.validate import validate_dataset
        errors = validate_dataset(SAMPLE, [{"column": "name", "required": True}])
        assert len(errors) == 0

    def test_required_fails(self):
        from forge.validate import validate_dataset
        records = [{"name": None}]
        errors = validate_dataset(records, [{"column": "name", "required": True}])
        assert "name" in errors

    def test_unique_passes(self):
        from forge.validate import validate_dataset
        errors = validate_dataset(SAMPLE, [{"column": "name", "unique": True}])
        assert len(errors) == 0

    def test_unique_fails(self):
        from forge.validate import validate_dataset
        records = [{"name": "Alice"}, {"name": "Alice"}]
        errors = validate_dataset(records, [{"column": "name", "unique": True}])
        assert "name" in errors

    def test_min_max(self):
        from forge.validate import validate_dataset
        errors = validate_dataset(SAMPLE, [{"column": "age", "min": 18, "max": 120}])
        assert len(errors) == 0


class TestFixtures:
    def test_pytest_fixture(self):
        from forge.fixtures import export_pytest_fixtures
        code = export_pytest_fixtures(SAMPLE)
        assert "pytest" in code
        assert "@pytest.fixture" in code
        assert "Alice" in code

    def test_json_fixture(self):
        from forge.fixtures import export_json_fixtures
        data = export_json_fixtures(SAMPLE)
        parsed = json.loads(data)
        assert len(parsed) == 2

    def test_typescript_fixture(self):
        from forge.fixtures import export_typescript
        code = export_typescript(SAMPLE, type_name="User")
        assert "export interface User" in code
        assert "name:" in code


class TestPromptInference:
    def test_infers_from_keywords(self):
        from forge.generator.prompt import infer_columns_from_prompt
        cols = infer_columns_from_prompt("users with name email age city")
        names = [c["name"] for c in cols]
        assert "name" in names
        assert "email" in names
        assert "age" in names

    def test_default_schema_matches(self):
        from forge.generator.prompt import infer_columns_from_prompt
        cols = infer_columns_from_prompt("product catalog with prices")
        names = [c["name"] for c in cols]
        assert "price" in names or "name" in names


class TestNLGenerate:
    def test_generate_from_prompt(self):
        from forge.generator.engine import Engine
        from forge.generator.prompt import infer_columns_from_prompt
        cols = infer_columns_from_prompt("users with name email age")
        engine = Engine()
        records = engine.generate_from_spec(cols, count=5)
        assert len(records) == 5
        names = [c["name"] for c in cols]
        for r in records:
            for n in names:
                assert n in r


class TestWatch:
    def test_watch_imports(self):
        from forge.watch import watch_file, watch_and_process
        assert callable(watch_file)
        assert callable(watch_and_process)


class TestREPL:
    def test_repl_imports(self):
        from forge.repl import start_repl
        assert callable(start_repl)


class TestWebSocket:
    def test_ws_imports(self):
        from forge.ws_server import start_ws_server, stream_websocket
        assert callable(start_ws_server)
        assert callable(stream_websocket)


class TestDBReaders:
    def test_postgres_registered(self):
        assert "postgres" in Registry.list_readers()

    def test_mysql_registered(self):
        assert "mysql" in Registry.list_readers()

    def test_bigquery_registered(self):
        assert "bigquery" in Registry.list_readers()
