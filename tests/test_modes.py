from forge.core.plugin import Registry


SAMPLE_RECORDS = [
    {"name": "Alice", "email": "alice@example.com", "age": 30, "phone": "555-123-4567"},
    {"name": "Bob", "email": "bob@test.com", "age": 25, "phone": "555-987-6543"},
]


class TestSynthesize:
    def test_generates_records(self):
        mode = Registry.get_mode("synthesize")()
        result = mode.run(SAMPLE_RECORDS, count=5)
        assert len(result) == 5
        assert all("name" in r for r in result)
        assert all("email" in r for r in result)

    def test_default_count(self):
        mode = Registry.get_mode("synthesize")()
        result = mode.run(SAMPLE_RECORDS)
        assert len(result) == 2


class TestAnonymize:
    def test_emails_anonymized(self):
        mode = Registry.get_mode("anonymize")()
        result = mode.run(SAMPLE_RECORDS)
        for r in result:
            assert r["email"] != "alice@example.com"
            assert "@" in r["email"]

    def test_phones_anonymized(self):
        mode = Registry.get_mode("anonymize")()
        result = mode.run(SAMPLE_RECORDS)
        for r in result:
            assert r["phone"] != "555-123-4567"


class TestRepair:
    def test_fills_nulls(self):
        records = [{"name": "Alice", "age": None}]
        mode = Registry.get_mode("repair")()
        result = mode.run(records)
        assert result[0]["age"] is not None


class TestScale:
    def test_scales_up(self):
        mode = Registry.get_mode("scale")()
        result = mode.run(SAMPLE_RECORDS, count=10)
        assert len(result) == 10

    def test_scales_down(self):
        mode = Registry.get_mode("scale")()
        result = mode.run(SAMPLE_RECORDS, count=1)
        assert len(result) == 1


class TestCompress:
    def test_compresses(self):
        mode = Registry.get_mode("compress")()
        result = mode.run(SAMPLE_RECORDS, count=1)
        assert len(result) == 1


class TestEnrich:
    def test_adds_fields(self):
        mode = Registry.get_mode("enrich")()
        result = mode.run(SAMPLE_RECORDS)
        for r in result:
            assert "_id" in r
            assert "_updated_at" in r
            assert "_checksum" in r


class TestStress:
    def test_adds_records(self):
        mode = Registry.get_mode("stress")()
        result = mode.run(SAMPLE_RECORDS, count=5)
        assert len(result) >= len(SAMPLE_RECORDS) + 5

    def test_works_with_empty(self):
        mode = Registry.get_mode("stress")()
        result = mode.run([], count=5)
        assert len(result) >= 5
