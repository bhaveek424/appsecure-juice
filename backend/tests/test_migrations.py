from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.migrations import migrate_sqlite_schema


def test_migrate_adds_disposition_to_existing_findings_table():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE findings (
                    id VARCHAR(36) PRIMARY KEY,
                    review_run_id VARCHAR(36) NOT NULL,
                    source VARCHAR(32) NOT NULL,
                    title VARCHAR(512) NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    severity VARCHAR(32) NOT NULL,
                    endpoint VARCHAR(2048) NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    remediation TEXT NOT NULL DEFAULT '',
                    confidence VARCHAR(64),
                    evidence_excerpt TEXT,
                    discovered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO findings (
                    id, review_run_id, source, title, category, severity,
                    endpoint, description, remediation
                ) VALUES (
                    'finding-1', 'run-1', 'Scanner', 'XSS', 'Cross Site Scripting',
                    'High', 'http://juice-shop:3000/', 'desc', 'fix'
                )
                """
            )
        )

    migrate_sqlite_schema(engine)

    with engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(findings)")).fetchall()
        }
        disposition = connection.execute(
            text("SELECT disposition FROM findings WHERE id = 'finding-1'")
        ).scalar_one()

    assert "disposition" in columns
    assert disposition == "Unreviewed"
