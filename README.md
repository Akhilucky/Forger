<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Akhilucky/Forger/main/.github/banner-dark.svg">
    <img alt="Forge" src="https://raw.githubusercontent.com/Akhilucky/Forger/main/.github/banner-light.svg" width="600">
  </picture>
</p>

<p align="center">
  <b>Universal data compiler — transform any input into production-ready datasets.</b>
</p>

<p align="center">
  <a href="#installation"><b>Install</b></a>
  •
  <a href="#cli-reference"><b>Commands</b></a>
  •
  <a href="#modes"><b>Modes</b></a>
  •
  <a href="#formats"><b>Formats</b></a>
  •
  <a href="#intelligent-generation"><b>Generation</b></a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Platform" src="https://img.shields.io/badge/platform-macOS%20%7C%20linux-lightgrey">
  <img alt="Tests" src="https://img.shields.io/badge/tests-78%20passing-brightgreen">
</p>

---

Forge doesn't simply generate fake data. It **analyzes, learns, restructures, repairs, anonymizes, enriches, converts, scales, synthesizes, validates, profiles, diffs, streams, and mocks** data while preserving its meaning and behavior.

| You give it | It gives you |
|---|---|
| A CSV file | A SQLite database |
| A JSON API dump | An anonymized Parquet file |
| A broken spreadsheet | A clean, typed dataset |
| 100 rows of data | 10M rows with realistic distributions |
| Column names | A million-row test file |
| A sentence | A structured dataset |

## Installation

```bash
pip install forge
```

Optional features:

```bash
pip install "forge[all]"         # everything below
pip install "forge[xlsx]"        # Excel support
pip install "forge[yaml]"        # YAML pipelines & schemas
pip install "forge[parquet]"     # Parquet format
pip install "forge[xml]"         # XML format
pip install "forge[postgres]"    # PostgreSQL reader/writer
pip install "forge[mysql]"       # MySQL reader
pip install "forge[bigquery]"    # Google BigQuery reader
pip install "forge[websocket]"   # WebSocket stream server
pip install "forge[watch]"       # File watching
```

## CLI Reference

### `forge generate`

Create datasets from column specs, natural language prompts, or sample files.

```bash
# From column names (infers types automatically)
forge generate --columns "name,email,age,salary,city" --count 100 -o data.json

# From a natural language description
forge generate --prompt "e-commerce customers with order history" --count 500

# Huge streaming files (no memory limit)
forge generate --columns "name,email,age" --size 1GB -o test.csv --format csv

# Learn patterns from existing data
forge generate --columns "name,email,age" --sample existing.csv --iterations 3

# Export as test fixtures
forge generate --columns "name,email,age" --count 5 --fixture pytest -o conftest.py
forge generate --columns "name,email,age" --count 5 --fixture typescript -o types.ts

# Use tiny local LLM for smarter generation
forge generate --columns "name,email,bio" --count 10 --llm
```

### `forge run`

Compile data or execute multi-step pipelines.

```bash
# One-shot conversion
forge run data.csv data.parquet
forge run customers.csv customers_clean.csv --mode anonymize

# Multi-step pipeline from YAML
forge run pipeline.yaml
```

Example `pipeline.yaml`:

```yaml
steps:
  - read: customers.csv
  - mode: anonymize
    columns: [email, phone, ssn]
  - mode: enrich
  - write: customers_clean.parquet
```

### `forge profile`

Generate an HTML data profile report — distributions, types, null ratios, top values.

```bash
forge profile data.csv -o report.html
forge profile large_data.parquet --title "Sales Data Overview"
```

### `forge diff`

Structurally compare two datasets.

```bash
forge diff old.csv new.csv
forge diff a.json b.json --key id    # key-based row matching
```

Reports: schema changes, row additions/removals, distribution shifts.

### `forge validate`

Validate datasets against rules.

```bash
forge validate data.csv --required "name,email" --unique "id,email"
forge validate data.csv --schema validation_rules.yaml
```

Example `rules.yaml`:
```yaml
- column: age
  required: true
  min: 0
  max: 120
  type: integer
- column: email
  required: true
  pattern: "@"
  unique: true
```

### `forge mock`

Start a local mock API server. Every plural noun becomes an endpoint.

```bash
forge mock                              # http://localhost:8000
forge mock --port 8080                  # custom port
forge mock --columns "id,name,email,age,city,company"
forge mock --schema schemas.yaml        # per-endpoint schemas

# Endpoints auto-create:
curl http://localhost:8000/users          # → 10 random users
curl http://localhost:8000/products       # → 10 random products
curl http://localhost:8000/orders         # → 10 random orders
curl http://localhost:8000/users/5        # → single user
curl http://localhost:8000/products?count=50
```

Built-in schemas: users, products, orders, customers, transactions, employees, posts.

### `forge watch`

Watch a file and re-process on every change.

```bash
forge watch data.csv output.csv --mode anonymize
forge watch logs/input.json output.parquet --interval 2
```

### `forge stream`

WebSocket server that streams generated records in real-time.

```bash
forge stream --port 8765 --columns "id,name,price,timestamp"
# Connect: ws://localhost:8765
# Receives 1 JSON record per second
```

### `forge shell`

Interactive Python REPL with Forge pre-loaded.

```bash
forge shell
>>> read("data.csv")
>>> gen(["name", "email", "age"], 10)
>>> profile(records, "My Data")
```

### `forge inspect`

Quick schema preview of any dataset.

```bash
forge inspect data.csv
forge inspect data.parquet --head 20
```

### `forge formats`

List all supported read/write formats.

## Formats

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
| PostgreSQL | ✓ | ✓ |
| MySQL | ✓ | |
| BigQuery | ✓ | |

## Modes

| Mode | Description |
|---|---|
| **generate** | Create datasets from scratch — column names, prompts, or samples |
| **mock** | Start a local mock API server (auto-endpoints from plural nouns) |
| **synthesize** | Generate statistically realistic synthetic data from a schema |
| **anonymize** | Remove or replace PII (emails, phones, SSNs, IPs) |
| **repair** | Fix missing values, correct types, normalize |
| **convert** | Translate between formats without losing semantics |
| **scale** | Expand datasets to millions of rows with realistic distributions |
| **compress** | Reduce datasets while preserving representative behavior |
| **enrich** | Add IDs, checksums, timestamps, metadata |
| **stress** | Generate edge cases, injections, adversarial inputs |

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
