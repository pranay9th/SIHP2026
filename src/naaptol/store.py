"""SQLite store for scan history, so the dashboard has something to show.

Also carries the repeat-offender ledger, which is what makes the escalating
penalty ladder in Section 36 of the Act usable: first offence, second offence,
subsequent offence each carry a different exposure, and you cannot apply that
without a queryable history.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import FAIL, ScanResult

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "scans.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at      TEXT NOT NULL,
    brand           TEXT,
    product         TEXT,
    category        TEXT,
    state           TEXT,
    district        TEXT,
    package_type    TEXT,
    pdp_area_cm2    REAL,
    overall         TEXT NOT NULL,
    fail_count      INTEGER NOT NULL,
    borderline_count INTEGER NOT NULL,
    indeterminate_count INTEGER NOT NULL,
    declarations_present INTEGER,
    scale_method    TEXT,
    scale_grade     TEXT,
    quality_grade   TEXT,
    rule_pack       TEXT,
    image_sha256    TEXT,
    facts_json      TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    rule_id     TEXT NOT NULL,
    citation    TEXT NOT NULL,
    title       TEXT NOT NULL,
    verdict     TEXT NOT NULL,
    severity    TEXT,
    reason      TEXT,
    measured    TEXT,
    required    TEXT
);

CREATE INDEX IF NOT EXISTS idx_scans_brand ON scans(brand);
CREATE INDEX IF NOT EXISTS idx_findings_rule ON findings(rule_id);
CREATE INDEX IF NOT EXISTS idx_findings_verdict ON findings(verdict);
"""


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(path) if path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save(conn: sqlite3.Connection, result: ScanResult, *,
         brand: str = "", product: str = "", category: str = "",
         state: str = "", district: str = "") -> int:
    cur = conn.execute(
        """INSERT INTO scans (
            scanned_at, brand, product, category, state, district,
            package_type, pdp_area_cm2, overall, fail_count,
            borderline_count, indeterminate_count, declarations_present,
            scale_method, scale_grade, quality_grade, rule_pack,
            image_sha256, facts_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            result.scanned_at or datetime.now().isoformat(timespec="seconds"),
            brand, product, category, state, district,
            result.context.package_type, result.context.pdp_area_cm2,
            result.overall, result.count("FAIL"),
            result.count("BORDERLINE"), result.count("INDETERMINATE"),
            result.declarations_present,
            result.scale.method, result.scale.grade,
            getattr(result.quality, "grade", None),
            result.rule_pack_version, result.image_sha256,
            json.dumps(result.facts.to_dict(), ensure_ascii=False),
        ),
    )
    scan_id = int(cur.lastrowid)

    conn.executemany(
        """INSERT INTO findings (
            scan_id, rule_id, citation, title, verdict, severity,
            reason, measured, required
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            (scan_id, f.rule_id, f.citation, f.title, f.verdict,
             f.severity, f.reason, f.measured, f.required)
            for f in result.findings
        ],
    )
    conn.commit()
    return scan_id


def offence_history(conn: sqlite3.Connection, brand: str) -> dict:
    """How many prior non-compliant scans this brand has.

    Maps onto Section 36: first offence up to Rs 25,000, second up to
    Rs 50,000, subsequent Rs 50,000 to Rs 1,00,000 with up to one year's
    imprisonment. The ladder is only usable with a history like this.
    """
    if not brand:
        return {"brand": brand, "prior": 0, "stage": "first", "exposure": "up to Rs 25,000"}

    row = conn.execute(
        "SELECT COUNT(*) AS n FROM scans WHERE brand = ? AND overall = 'NON-COMPLIANT'",
        (brand,),
    ).fetchone()
    prior = int(row["n"])

    if prior <= 1:
        stage, exposure = "first", "up to Rs 25,000"
    elif prior == 2:
        stage, exposure = "second", "up to Rs 50,000"
    else:
        stage, exposure = ("subsequent",
                           "Rs 50,000 to Rs 1,00,000 and/or imprisonment up to 1 year")
    return {"brand": brand, "prior": prior, "stage": stage, "exposure": exposure}


def summary(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) n FROM scans").fetchone()["n"]
    by_overall = {
        r["overall"]: r["n"] for r in conn.execute(
            "SELECT overall, COUNT(*) n FROM scans GROUP BY overall")
    }
    top_rules = [
        dict(r) for r in conn.execute(
            """SELECT citation, title, COUNT(*) n FROM findings
               WHERE verdict = 'FAIL' GROUP BY rule_id
               ORDER BY n DESC LIMIT 10"""
        )
    ]
    by_brand = [
        dict(r) for r in conn.execute(
            """SELECT brand, COUNT(*) scans,
                      SUM(CASE WHEN overall='NON-COMPLIANT' THEN 1 ELSE 0 END) fails
               FROM scans WHERE brand <> '' GROUP BY brand
               ORDER BY fails DESC, scans DESC LIMIT 15"""
        )
    ]
    by_state = [
        dict(r) for r in conn.execute(
            """SELECT state, COUNT(*) scans,
                      SUM(CASE WHEN overall='NON-COMPLIANT' THEN 1 ELSE 0 END) fails
               FROM scans WHERE state <> '' GROUP BY state ORDER BY fails DESC"""
        )
    ]
    return {"total": total, "by_overall": by_overall, "top_rules": top_rules,
            "by_brand": by_brand, "by_state": by_state}
