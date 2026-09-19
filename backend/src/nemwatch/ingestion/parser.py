import csv
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from nemwatch.domain.models import DispatchRecord, Region, RejectedRow

REQUIRED_COLUMNS = ("region", "interval_datetime", "price", "demand")
DECIMAL_COLUMNS = ("price", "demand", "generation", "interchange")


@dataclass(frozen=True)
class ParseResult:
    records: tuple[DispatchRecord, ...]
    rejected: tuple[RejectedRow, ...]


def _context(row: dict[str, str | None]) -> dict[str, str]:
    return {key: str(row.get(key, ""))[:80] for key in ("region", "interval_datetime") if row.get(key)}


def _reject(source_row: int, code: str, message: str, row: dict[str, str | None]) -> RejectedRow:
    return RejectedRow(source_row=source_row, reason_code=code, message=message, context=_context(row))


def parse_dispatch_csv(content: str, source: str) -> ParseResult:
    reader = csv.DictReader(io.StringIO(content))
    missing_headers = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
    if missing_headers:
        return ParseResult(records=(), rejected=(RejectedRow(
            source_row=1, reason_code="missing_field",
            message=f"Missing required columns: {', '.join(missing_headers)}",
        ),))

    records: list[DispatchRecord] = []
    rejected: list[RejectedRow] = []
    for source_row, row in enumerate(reader, start=2):
        missing = [column for column in REQUIRED_COLUMNS if not (row.get(column) or "").strip()]
        if missing:
            rejected.append(_reject(source_row, "missing_field", f"Missing: {', '.join(missing)}", row))
            continue
        try:
            region = Region((row["region"] or "").strip())
        except ValueError:
            rejected.append(_reject(source_row, "invalid_region", "Unsupported NEM region", row))
            continue
        try:
            interval = datetime.fromisoformat((row["interval_datetime"] or "").replace("Z", "+00:00"))
            if interval.tzinfo is None or interval.utcoffset() is None:
                raise ValueError
        except ValueError:
            rejected.append(_reject(source_row, "invalid_timestamp", "Timestamp must include an offset", row))
            continue
        values: dict[str, Decimal | None] = {}
        decimal_error: str | None = None
        for column in DECIMAL_COLUMNS:
            raw = (row.get(column) or "").strip()
            if not raw and column in {"generation", "interchange"}:
                values[column] = None
                continue
            try:
                value = Decimal(raw)
            except InvalidOperation:
                decimal_error = "invalid_decimal"
                break
            if not value.is_finite():
                decimal_error = "non_finite_decimal"
                break
            values[column] = value
        if decimal_error:
            rejected.append(_reject(source_row, decimal_error, "Invalid numeric value", row))
            continue
        records.append(DispatchRecord(
            region=region, interval_datetime=interval,
            price=values["price"], demand=values["demand"],  # type: ignore[arg-type]
            generation=values["generation"], interchange=values["interchange"],
            source_file=source, source_row=source_row,
        ))
    return ParseResult(records=tuple(records), rejected=tuple(rejected))
