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

# Generate 1K records from column specs
forge generate --columns "name,email,age,salary,city" --count 1000 -o data.json

# Generate a 1GB CSV file (streaming, no memory limit)
forge generate --columns "name,email,age,salary,city,company" --size 1GB -o huge.csv --format csv

# Start a mock API server
forge mock

# Mock API with custom schema
forge mock --columns "id,name,email,age,city" --port 8080

# Generate from specs + learn patterns from a sample
forge generate --columns "name,email,age" --sample existing.csv --count 5000

# Self-iterate for quality
forge generate --columns "name,email,age" --count 100 --iterations 3

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

# Or generate from scratch
from forge.generator.engine import Engine
engine = Engine()
records = engine.generate_from_spec(
    columns=[
        {"name": "name", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "age", "type": "integer"},
    ],
    count=500,
)

# Stream huge dataset to disk
from forge.generator.stream import generate_huge
generate_huge(
    columns=[{"name": "name"}, {"name": "email"}, {"name": "age"}],
    destination="test_data.csv",
    target_size="100MB",
    fmt="csv",
)
```

### Mock API

```bash
# Start server — endpoints auto-create from any plural noun
forge mock

# In another terminal:
curl http://localhost:8000/users          # 10 random users
curl http://localhost:8000/users/5         # single user with id=5
curl http://localhost:8000/products        # 10 random products
curl http://localhost:8000/products?count=50  # 50 products
curl http://localhost:8000/orders          # auto-schema for "orders"
curl http://localhost:8000/customers       # auto-schema for "customers"

# Custom column schema for all endpoints
forge mock --columns "id,name,email,age,city,company,title"

# Custom schema per endpoint (YAML file)
forge mock --schema schemas.yaml

# POST requests echo back as "created"
curl -X POST http://localhost:8000/users -H 'Content-Type: application/json' \
  -d '{"name": "New User"}'
```

### Huge Test Files

```bash
# Target file size, not row count
forge generate --columns "name,email,age,salary,city,company" --size 1GB -o test.csv --format csv

# NDJSON for easy line-by-line processing
forge generate --columns "id,name,email" --size 500MB -o test.ndjson --format ndjson

# SQL dump
forge generate --columns "id,name,email" --size 100MB -o test.sql --format sql
```

The `--size` flag uses row-by-row streaming, so it never loads the full dataset into memory.
A progress indicator shows rows written and current file size.

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
| **generate** | Create datasets from scratch using just column names — infers realistic types, supports `--size` for huge files, `--iterations` for quality |
| **mock** | Start a local mock API server — each plural noun becomes an auto-generated endpoint |
| **synthesize** | Generate statistically realistic synthetic data from an existing schema |
| **anonymize** | Remove or replace PII (emails, phones, SSNs, IPs) while preserving structure |
| **repair** | Fix missing values, correct types, normalize formats |
| **convert** | Translate between formats without losing semantics |
| **scale** | Expand datasets from hundreds to millions of rows with realistic distributions |
| **compress** | Reduce large datasets while preserving representative behavior |
| **enrich** | Add IDs, checksums, timestamps and metadata |
| **stress** | Generate edge cases, injections, and adversarial inputs for robustness testing |

## Intelligent Generation

The `generate` engine understands column names to produce contextually appropriate data:

| Column name hint | Generates |
|---|---|
| `name`, `first_name`, `last_name` | Realistic person names |
| `email` | Realistic email addresses |
| `phone`, `mobile` | US phone numbers |
| `address`, `street` | Street addresses |
| `city`, `state`, `country`, `zip` | Geographic data |
| `company`, `organization` | Company names |
| `job`, `title`, `role` | Job titles |
| `age` | Ages (18–80) |
| `price`, `salary`, `cost` | Financial values |
| `url`, `website` | URLs |
| `description`, `comment`, `notes` | Descriptive paragraphs |
| `category`, `type`, `status` | Categorical values |
| `date`, `created_at`, `timestamp` | Date/time strings |
| `gender` | Gender values |

From sample data, it additionally infers:
- **Distributions** — normal, categorical, or uniform
- **Patterns** — regex-based structural templates
- **Correlations** — preserves relationships between numeric columns

Optional LLM backend (`--llm` flag) uses **tiny local models** (Phi-3, Llama-3.2-3B via Ollama or llama.cpp) for even more realistic generation — zero API costs.

## Philosophy

**Data is source code. Forge compiles it.**

Any format. Any scale. Any domain. Real enough to build. Safe enough to share.

## License

MIT
