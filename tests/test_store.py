"""Scan history and the repeat-offender ledger."""
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naaptol import store  # noqa: E402
from naaptol.models import (  # noqa: E402
    FAIL, PASS, Finding, LabelFacts, PackageContext, ScaleEstimate, ScanResult,
)


def make_result(overall_fail: bool) -> ScanResult:
    findings = [
        Finding(rule_id="LMPC.R6.1.c.net_quantity", citation="Rule 6(1)(c)",
                title="Net quantity", verdict=PASS, severity="critical",
                reason="Found"),
    ]
    if overall_fail:
        findings.append(Finding(
            rule_id="LMPC.R7.2.letter_height", citation="Rule 7(2)",
            title="Minimum height of letters and numerals", verdict=FAIL,
            severity="critical", reason="1.86 mm below 2.5 mm",
            measured="1.86 mm", required="2.5 mm",
        ))
    return ScanResult(
        findings=findings,
        facts=LabelFacts(raw_text="x", net_quantity="200 g", mrp="Rs.40"),
        context=PackageContext(pdp_area_cm2=108),
        scale=ScaleEstimate(0.0833, "aruco_rectified", "measurement", 0.03),
        rule_pack_version="1.0.0",
        scanned_at="2026-09-04T10:00:00",
    )


@pytest.fixture
def conn(tmp_path):
    return store.connect(tmp_path / "test.db")


def test_save_and_summarise(conn):
    store.save(conn, make_result(True), brand="Meethi Foods", state="MP")
    store.save(conn, make_result(False), brand="Sunrise Foods", state="MH")
    data = store.summary(conn)
    assert data["total"] == 2
    assert data["by_overall"]["NON-COMPLIANT"] == 1
    assert data["by_overall"]["COMPLIANT"] == 1
    assert data["top_rules"][0]["citation"] == "Rule 7(2)"


class TestOffenceLadder:
    """Section 36 escalates by offence number, so history has to be queryable."""

    def test_first_offence(self, conn):
        store.save(conn, make_result(True), brand="Acme")
        assert store.offence_history(conn, "Acme")["stage"] == "first"

    def test_second_offence(self, conn):
        for _ in range(2):
            store.save(conn, make_result(True), brand="Acme")
        history = store.offence_history(conn, "Acme")
        assert history["stage"] == "second"
        assert "50,000" in history["exposure"]

    def test_subsequent_offence_carries_imprisonment_exposure(self, conn):
        for _ in range(4):
            store.save(conn, make_result(True), brand="Acme")
        history = store.offence_history(conn, "Acme")
        assert history["stage"] == "subsequent"
        assert "imprisonment" in history["exposure"]

    def test_compliant_scans_do_not_count_as_offences(self, conn):
        for _ in range(5):
            store.save(conn, make_result(False), brand="Acme")
        assert store.offence_history(conn, "Acme")["prior"] == 0

    def test_unknown_brand_is_treated_as_first_offence(self, conn):
        assert store.offence_history(conn, "")["stage"] == "first"


def test_connection_is_usable_from_another_thread(tmp_path):
    """Regression test for a bug that broke the dashboard on its second view.

    Streamlit runs every script rerun on a fresh thread and the app caches this
    connection, so SQLite's default same-thread guard raised ProgrammingError
    as soon as a second page view arrived.
    """
    conn = store.connect(tmp_path / "threaded.db")
    store.save(conn, make_result(True), brand="Acme")

    errors: list[Exception] = []
    totals: list[int] = []

    def read():
        try:
            totals.append(store.summary(conn)["total"])
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=read)
    thread.start()
    thread.join()

    assert not errors, f"cross-thread access failed: {errors}"
    assert totals == [1]
