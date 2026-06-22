from forge.core.plugin import Registry
from forge.generator.engine import Engine
from forge.generator.inference import ColumnProfile, guess_field_type
from forge.generator.fields import generate as gen_field


SAMPLE = [
    {"name": "Alice Smith", "email": "alice@example.com", "age": 30, "salary": 85000},
    {"name": "Bob Johnson", "email": "bob@test.com", "age": 25, "salary": 62000},
    {"name": "Carol Williams", "email": "carol@demo.org", "age": 35, "salary": 95000},
]


class TestGuessFieldType:
    def test_name(self):
        assert guess_field_type("first_name") == "name"
        assert guess_field_type("fullname") == "name"

    def test_email(self):
        assert guess_field_type("email") == "email"
        assert guess_field_type("e_mail") == "email"

    def test_phone(self):
        assert guess_field_type("phone_number") == "phone"
        assert guess_field_type("mobile") == "phone"

    def test_address(self):
        assert guess_field_type("address") == "address"
        assert guess_field_type("street_address") == "address"

    def test_unknown(self):
        assert guess_field_type("xyz_abc") is None


class TestColumnProfile:
    def test_numeric_distribution(self):
        prof = ColumnProfile("age", [v["age"] for v in SAMPLE])
        assert prof.distribution["kind"] == "normal"
        assert "mu" in prof.distribution

    def test_categorical_distribution(self):
        prof = ColumnProfile("status", ["A", "A", "B", "C", "A", "B"])
        assert prof.distribution["kind"] == "categorical"
        assert "A" in prof.distribution["categories"]

    def test_hint_inferred(self):
        prof = ColumnProfile("email", [v["email"] for v in SAMPLE])
        assert prof.hint == "email"


class TestFieldGeneration:
    def test_email_generation(self):
        val = gen_field(None, "email", None, "email_addr")
        assert "@" in val
        assert "." in val.split("@")[1]

    def test_phone_generation(self):
        val = gen_field(None, "phone", None, "phone")
        assert "+1" in val or val.replace(" ", "")[0].isdigit()

    def test_name_generation(self):
        val = gen_field(None, "name", None, "full_name")
        assert " " in val
        assert len(val) > 3

    def test_numeric_generation(self):
        val = gen_field(None, "age", {"kind": "normal", "mu": 30, "sigma": 5, "min": 18, "max": 80}, "age")
        assert isinstance(val, int)
        assert 10 <= val <= 90

    def test_url_generation(self):
        val = gen_field(None, "url", None, "website")
        assert val.startswith("https://")


class TestEngine:
    def test_generates_records(self):
        engine = Engine().learn(SAMPLE)
        records = engine.generate(count=5)
        assert len(records) == 5
        assert all("name" in r for r in records)
        assert all("email" in r for r in records)

    def test_generates_from_spec(self):
        engine = Engine()
        columns = [
            {"name": "first_name", "type": "string"},
            {"name": "age", "type": "integer"},
        ]
        records = engine.generate_from_spec(columns, count=3)
        assert len(records) == 3
        for r in records:
            assert "first_name" in r
            assert "age" in r

    def test_learns_from_sample(self):
        engine = Engine().learn(SAMPLE)
        records = engine.generate(count=10)
        emails = [r.get("email") for r in records]
        assert all("@" in e for e in emails if e)


class TestGenerateMode:
    def test_mode_registered(self):
        assert "generate" in Registry.list_modes()

    def test_generates_with_sample(self):
        mode = Registry.get_mode("generate")()
        result = mode.run(SAMPLE, count=5)
        assert len(result) == 5
        assert all("name" in r for r in result)
        assert all("email" in r for r in result)

    def test_generates_empty(self):
        mode = Registry.get_mode("generate")()
        result = mode.run([], count=3)
        assert len(result) == 3

    def test_self_iterates(self):
        mode = Registry.get_mode("generate")()
        result = mode.run(SAMPLE, count=5, iterations=2)
        assert len(result) == 5
