from pathlib import Path

from nemwatch.ingestion.parser import parse_dispatch_csv


def test_fixture_keeps_valid_rows_and_types_rejections() -> None:
    fixture = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "dispatch_sample.csv"
    result = parse_dispatch_csv(fixture.read_text(encoding="utf-8"), fixture.name)
    assert len(result.records) == 15
    assert [item.reason_code for item in result.rejected] == [
        "invalid_timestamp", "invalid_region", "invalid_decimal", "missing_field"
    ]


def test_bad_row_does_not_suppress_following_valid_row() -> None:
    content = "region,interval_datetime,price,demand\nBAD,now,x,x\nQLD1,2026-01-01T00:00:00Z,1,2\n"
    result = parse_dispatch_csv(content, "test.csv")
    assert len(result.records) == 1
    assert len(result.rejected) == 1


def test_non_finite_decimal_has_distinct_code() -> None:
    content = "region,interval_datetime,price,demand\nQLD1,2026-01-01T00:00:00Z,NaN,2\n"
    assert parse_dispatch_csv(content, "test.csv").rejected[0].reason_code == "non_finite_decimal"
