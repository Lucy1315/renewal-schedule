from __future__ import annotations

import csv
from pathlib import Path

from models import SendRecord

LOG_COLUMNS = [
    "run_datetime",
    "category",
    "target_year_month",
    "item_count",
    "status",
    "error_message",
    "recipients",
]


def init_log_file(log_path: str | Path) -> None:
    """로그 파일이 없으면 헤더만 있는 빈 파일 생성."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(LOG_COLUMNS)


def read_send_history(log_path: str | Path) -> list[SendRecord]:
    """발송 이력 전체 로드."""
    path = Path(log_path)
    if not path.exists():
        return []
    records: list[SendRecord] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                SendRecord(
                    run_datetime=row["run_datetime"],
                    category=row["category"],
                    target_year_month=row["target_year_month"],
                    item_count=int(row["item_count"]),
                    status=row["status"],
                    error_message=row["error_message"],
                    recipients=row["recipients"],
                )
            )
    return records


def append_send_record(log_path: str | Path, record: SendRecord) -> None:
    """발송 이력 1건 추가."""
    path = Path(log_path)
    init_log_file(path)
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            record.run_datetime,
            record.category,
            record.target_year_month,
            record.item_count,
            record.status,
            record.error_message,
            record.recipients,
        ])


def has_been_sent(
    log_path: str | Path,
    category: str,
    target_year_month: str,
) -> bool:
    """멱등성 체크: 동일 category + target_year_month에 SUCCESS 기록이 있으면 True."""
    records = read_send_history(log_path)
    return any(
        r.category == category
        and r.target_year_month == target_year_month
        and r.status == "SUCCESS"
        for r in records
    )
