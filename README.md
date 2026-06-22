<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Akhilucky/Faker/main/.github/banner-dark.svg">
    <img alt="Forge" src="https://raw.githubusercontent.com/Akhilucky/Faker/main/.github/banner-light.svg" width="600">
  </picture>
</p>

<p align="center">
  <b>Universal data compiler — transform any input into production-ready datasets.</b>
</p>

<p align="center">
  <a href="#installation"><b>Install</b></a>
  •
  <a href="#usage"><b>Usage</b></a>
  •
  <a href="#modes"><b>Modes</b></a>
  •
  <a href="#formats"><b>Formats</b></a>
  •
  <a href="#development"><b>Development</b></a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Platform" src="https://img.shields.io/badge/platform-macOS%20%7C%20linux-lightgrey">
</p>

---

Forge doesn't simply generate fake data. It **analyzes, learns, restructures, repairs, anonymizes, enriches, converts, scales and synthesizes** data while preserving its meaning and behavior.

| You give it | It gives you |
|---|---|
| A CSV file | A SQLite database |
| A JSON API dump | An anonymized Parquet file |
| A broken spreadsheet | A clean, typed dataset |
| 100 rows of data | 10M rows with realistic distributions |
| Production logs | A synthetic training corpus |

## Installation

```bash
pip install forge
```

With format support:

```bash
pip install "forge[all]"        # everything
pip install "forge[xlsx]"       # Excel support
pip install "forge[yaml]"       # YAML support
pip install "forge[parquet]"    # Parquet support
pip install "forge[xml]"        # XML support
```

## Usage

### CLI

```bash
# Convert CSV → JSON
forge run data.csv data.json

# Apply anonymization
forge run customers.csv customers_clean.csv --mode anonymize

# Synthesize 10K records from a schema
forge run schema.csv generated.json --mode synthesize --count 10000

# Scale 100 rows → 1M rows
forge run small.csv big.parquet --mode scale --count 1000000

# Inspect a dataset
forge inspect data.csv
```

### Python API

```python
from forge.core.pipeline import Pipeline

records = (
    Pipeline()
    .read("data.csv")
    .apply("anonymize", columns=["email", "phone"])
    .apply("enrich")
    .write("clean_data.json")
    .run()
)
```

### Formats

| Format | Read | Write |
|---|---|---|
| CSV | ✓ | ✓ |
| JSON | ✓ | ✓ |
| NDJSON | ✓ | ✓ |
| XLSX | ✓ | ✓ |
| YAML | ✓ | ✓ |
| XML | ✓ | ✓ |
| Parquet | ✓ | ✓ |
| SQLite | ✓ | ✓ |
| SQL | | ✓ |
| Markdown | ✓ | ✓ |
| HTML | ✓ | |
| Plain text | ✓ | |

## Modes

| Mode | Description |
|---|---|
| **synthesize** | Generate statistically realistic synthetic data from an existing schema |
| **anonymize** | Remove or replace PII (emails, phones, SSNs, IPs) while preserving structure |
| **repair** | Fix missing values, correct types, normalize formats |
| **convert** | Translate between formats without losing semantics |
| **scale** | Expand datasets from hundreds to millions of rows with realistic distributions |
| **compress** | Reduce large datasets while preserving representative behavior |
| **enrich** | Add IDs, checksums, timestamps and metadata |
| **stress** | Generate edge cases, injections, and adversarial inputs for robustness testing |

## Philosophy

**Data is source code. Forge compiles it.**

Any format. Any scale. Any domain. Real enough to build. Safe enough to share.

## License

MIT
