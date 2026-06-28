from __future__ import annotations

from typing import Any

from forge.core.plugin import Registry, Reader, Writer


@Registry.register_reader
class PostgresReader(Reader):
    formats = ["postgres", "postgresql", "pg"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            try:
                import pg8000 as psycopg2
            except ImportError:
                raise ImportError("psycopg2 or pg8000 required for Postgres. pip install psycopg2-binary")
        conn = psycopg2.connect(source)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = kwargs.get("query", kwargs.get("table"))
        if not query:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 1")
            tables = cur.fetchall()
            if not tables:
                conn.close()
                return []
            query = f"SELECT * FROM {tables[0]['table_name']}"
        cur.execute(query)
        results = [dict(r) for r in cur.fetchall()]
        conn.close()
        return results


@Registry.register_reader
class MySQLReader(Reader):
    formats = ["mysql", "mariadb"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            import mysql.connector
        except ImportError:
            raise ImportError("mysql-connector-python required for MySQL. pip install mysql-connector-python")
        conn = mysql.connector.connect(**parse_mysql_dsn(source))
        cur = conn.cursor(dictionary=True)
        query = kwargs.get("query", kwargs.get("table"))
        if not query:
            cur.execute("SELECT DATABASE()")
            db = cur.fetchone()
            cur.execute(f"SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema='{db[0]}' LIMIT 1")
            tables = cur.fetchall()
            if not tables:
                conn.close()
                return []
            query = f"SELECT * FROM {tables[0]['TABLE_NAME']}"
        cur.execute(query)
        results = [dict(r) for r in cur.fetchall()]
        conn.close()
        return results


@Registry.register_reader
class BigQueryReader(Reader):
    formats = ["bigquery", "bq"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            from google.cloud import bigquery
        except ImportError:
            raise ImportError("google-cloud-bigquery required. pip install google-cloud-bigquery")
        client = bigquery.Client()
        query = kwargs.get("query", kwargs.get("table", source))
        results = client.query(query).result()
        return [dict(r) for r in results]


@Registry.register_writer
class PostgresWriter(Writer):
    format = "postgres"

    def write(self, records: list[dict], destination: str, **kwargs) -> None:
        table = kwargs.get("table", "data")
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 required. pip install psycopg2-binary")
        conn = psycopg2.connect(destination)
        cur = conn.cursor()
        if records:
            cols = list(records[0].keys())
            placeholders = ",".join("%s" for _ in cols)
            col_list = ",".join(cols)
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_list})")
            for r in records:
                cur.execute(
                    f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
                    [r.get(c) for c in cols],
                )
        conn.commit()
        conn.close()


def parse_mysql_dsn(dsn: str) -> dict:
    parts = dsn.replace("mysql://", "").split("/")
    user_pass = parts[0].split("@")[0] if "@" in parts[0] else ""
    host_port = parts[0].split("@")[-1] if "@" in parts[0] else parts[0]
    db = parts[1] if len(parts) > 1 else ""
    user = user_pass.split(":")[0] if ":" in user_pass else user_pass
    password = user_pass.split(":")[1] if ":" in user_pass else ""
    host = host_port.split(":")[0] if ":" in host_port else host_port
    port = int(host_port.split(":")[1]) if ":" in host_port else 3306
    return {"host": host, "port": port, "user": user, "password": password, "database": db}
