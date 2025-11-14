"""Lightweight database utilities shared across agents."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Tuple

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv(override=True)


def _connect() -> pymysql.connections.Connection:
    """Create a new MySQL connection using environment variables."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", os.getenv("MYSQL_HOST", "localhost")),
        user=os.getenv("DB_USER", os.getenv("MYSQL_USER", "root")),
        password=os.getenv("DB_PASSWORD", os.getenv("MYSQL_PASSWORD", "")),
        database=os.getenv("DB_NAME", os.getenv("MYSQL_DATABASE", "Fin")),
        port=int(os.getenv("DB_PORT", os.getenv("MYSQL_PORT", "3306"))),
        cursorclass=DictCursor,
        charset="utf8mb4",
        autocommit=False,
    )


@contextmanager
def db_cursor() -> Generator[Tuple[pymysql.connections.Connection, DictCursor], None, None]:
    """Context manager that yields a connection and cursor and handles commit/rollback."""
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
