import pandas as pd
import io
import os
import psycopg2

from pathlib import Path
from typing import List
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import make_dsn


def connection_string() -> str:
    """
        Builds the PostgreSQL connection string from recommender/.env so the password never appears in code.
        Only POSTGRES_PASSWORD is required; host, port, user and database default to the local Docker container.
    """
    load_dotenv(Path(__file__).parent / ".env")
    return make_dsn(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        password=os.environ["POSTGRES_PASSWORD"],
    )

def fast_pg_insert(df: pd.DataFrame, connection: str, table_name: str, columns: List[str]) -> None:
    """
        Inserts data from a pandas DataFrame into a PostgreSQL table using the COPY command for fast insertion.

        Parameters:
        df (pd.DataFrame): The DataFrame containing the data to be inserted.
        connection (str): The connection string to the PostgreSQL database.
        table_name (str): The name of the target table in the PostgreSQL database.
        columns (List[str]): A list of column names in the target table that correspond to the DataFrame columns.

        Returns:
        None
    """
    conn = psycopg2.connect(connection)
    _buffer = io.StringIO()
    df.to_csv(_buffer, index=False, header=False)
    _buffer.seek(0)
    # COPY must read CSV format to match to_csv. copy_from reads Postgres's text format, which doesn't
    # understand CSV quoting, so a value like 'He said "hi"' would be stored as '"He said ""hi"""'
    copy = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv)").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    with conn.cursor() as c:
        c.copy_expert(copy.as_string(conn), _buffer)
    conn.commit()
    conn.close()