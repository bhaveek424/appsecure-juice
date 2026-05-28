from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.domain.review_disposition import ReviewDisposition

DEFAULT_DISPOSITION = ReviewDisposition.UNREVIEWED


def _sqlite_table_names(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
    return {row[0] for row in rows}


def _sqlite_column_names(engine: Engine, table_name: str) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(f"PRAGMA table_info({table_name})")
        ).fetchall()
    return {row[1] for row in rows}


def migrate_sqlite_schema(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    tables = _sqlite_table_names(engine)
    if "findings" not in tables:
        return

    columns = _sqlite_column_names(engine, "findings")
    if "disposition" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE findings "
                f"ADD COLUMN disposition VARCHAR(32) NOT NULL "
                f"DEFAULT '{DEFAULT_DISPOSITION}'"
            )
        )
        connection.execute(
            text(
                "UPDATE findings "
                f"SET disposition = '{DEFAULT_DISPOSITION}' "
                "WHERE disposition IS NULL"
            )
        )
