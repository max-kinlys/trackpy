from __future__ import annotations

from pathlib import Path

import csv
import pytest

from trackpy.transponder import read_transponder


REQUIRED_COLUMNS = {
    "Timestamp",
    "Session",
    "Lap",
    "Laptime (s)",
    "Average speed (m/s)",
    "Distance (m)",
}


def _data_path(filename: str) -> Path:
    return Path(__file__).parent / "data" / filename


def _write_csv(path: Path, rows: list[dict[str, str]], encoding: str) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_read_transponder_columns_from_fixture():
    df = read_transponder(_data_path("sessions_7213814594.csv"))

    assert set(df.columns) == REQUIRED_COLUMNS


def test_read_transponder_ignores_extra_columns_and_sessions(tmp_path):
    rows = [
        {
            "Date": "01-01-2024",
            "Start time": "12:00:00",
            "Total time": "00:00:10",
            "Laptime": "00:00:10",
            "Speed": "36 km/h",
            "Lap": "1",
            "Diff": "00:00:00",
            "Transponder": "ABC123",
            "H1": "foo",
            "H2": "bar",
        },
        {
            "Date": "01-01-2024",
            "Start time": "12:00:10",
            "Total time": "00:00:20",
            "Laptime": "00:00:10",
            "Speed": "36 km/h",
            "Lap": "2",
            "Diff": "00:00:10",
            "Transponder": "ABC123",
            "H1": "foo",
            "H2": "bar",
        },
        {
            "Date": "01-01-2024",
            "Start time": "12:00:30",
            "Total time": "00:00:30",
            "Laptime": "00:00:12",
            "Speed": "30 km/h",
            "Lap": "4",
            "Diff": "00:00:20",
            "Transponder": "ABC123",
            "H1": "foo",
            "H2": "bar",
        },
        {
            "Date": "01-01-2024",
            "Start time": "12:00:42",
            "Total time": "00:00:42",
            "Laptime": "00:00:12",
            "Speed": "30 km/h",
            "Lap": "5",
            "Diff": "00:00:12",
            "Transponder": "ABC123",
            "H1": "foo",
            "H2": "bar",
        },
    ]

    csv_path = tmp_path / "transponder_extra_columns.csv"
    _write_csv(csv_path, rows, encoding="utf-16-le")

    df = read_transponder(csv_path)

    assert set(df.columns) == REQUIRED_COLUMNS
    assert "H1" not in df.columns
    assert "H2" not in df.columns
    assert df["Session"].tolist() == [1, 1, 2, 2]


def test_read_transponder_rejects_non_utf16le(tmp_path):
    rows = [
        {
            "Date": "01-01-2024",
            "Start time": "12:00:00",
            "Total time": "00:00:10",
            "Laptime": "00:00:10",
            "Speed": "36 km/h",
            "Lap": "1",
            "Diff": "00:00:00",
            "Transponder": "ABC123",
        }
    ]

    csv_path = tmp_path / "transponder_utf8.csv"
    _write_csv(csv_path, rows, encoding="utf-8")

    with pytest.raises(ValueError, match="utf-16-le CSV"):
        read_transponder(csv_path)
