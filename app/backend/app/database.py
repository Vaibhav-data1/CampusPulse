import os
import sqlite3
from collections.abc import Generator
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "campuspulse.db"


def get_database_path() -> Path:
    return Path(os.getenv("CAMPUSPULSE_DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def get_connection() -> sqlite3.Connection:
    path = get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                severity INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
                description TEXT NOT NULL,
                observed_at TEXT,
                approximate_location_id TEXT,
                crowd_level INTEGER CHECK (crowd_level IS NULL OR crowd_level BETWEEN 1 AND 5),
                environmental_rating INTEGER CHECK (
                    environmental_rating IS NULL OR environmental_rating BETWEEN 1 AND 5
                )
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(observations)")
        }
        migrations = {
            "observed_at": "ALTER TABLE observations ADD COLUMN observed_at TEXT",
            "approximate_location_id": (
                "ALTER TABLE observations ADD COLUMN approximate_location_id TEXT"
            ),
            "crowd_level": "ALTER TABLE observations ADD COLUMN crowd_level INTEGER",
            "environmental_rating": (
                "ALTER TABLE observations ADD COLUMN environmental_rating INTEGER"
            ),
        }
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(statement)
        connection.commit()
