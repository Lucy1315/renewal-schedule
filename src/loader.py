from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path

from models import DeviceItem, MedicineItem, edate

logger = logging.getLogger(__name__)


def parse_date(text: str) -> date:
    """'YYYY-MM-DD' 문자열을 date로 변환."""
    return date.fromisoformat(text.strip())


def parse_date_range(text: str) -> tuple[date, date]:
    """'YYYY-MM-DD ~ YYYY-MM-DD' → (시작일, 종료일)"""
    parts = text.split("~")
    if len(parts) != 2:
        raise ValueError(f"날짜 범위 파싱 실패: '{text}'")
    return parse_date(parts[0]), parse_date(parts[1])


def load_medicine_csv(path: str | Path) -> list[MedicineItem]:
    """의약품 CSV 로딩. 알림발송일 = edate(갱신신청기한, -3), 알림발송일_1M = edate(갱신신청기한, -1)."""
    items: list[MedicineItem] = []
    path = Path(path)

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            try:
                갱신신청기한 = parse_date(row["갱신신청기한"])
                item = MedicineItem(
                    제품명=row["제품명"].strip(),
                    허가일=parse_date(row["허가일"]),
                    품목유효기간=parse_date(row["품목유효기간"]),
                    갱신신청기한=갱신신청기한,
                    알림발송일=edate(갱신신청기한, -3),
                    알림발송일_1M=edate(갱신신청기한, -1),
                    업종=row["업종"].strip(),
                    제조수입=row["제조/수입"].strip(),
                    허가번호=row["허가번호"].strip(),
                    품목기준코드=row["품목기준코드"].strip(),
                    전문일반=row["전문/일반"].strip(),
                    품목분류=row["품목분류"].strip(),
                    허가신고=row["허가/신고"].strip(),
                    유효기간=row["유효기간"].strip(),
                    관계부처=row["관계부처"].strip(),
                    row_index=idx,
                )
                items.append(item)
            except Exception as e:
                logger.warning("의약품 행 %d 파싱 실패: %s", idx, e)

    logger.info("의약품 %d건 로드 완료 (경로: %s)", len(items), path)
    return items


def load_device_csv(path: str | Path) -> list[DeviceItem]:
    """의료기기 CSV 로딩. 알림발송일 = edate(갱신신청기한_시작, -3), 알림발송일_1M = edate(갱신신청기한_시작, -1)."""
    items: list[DeviceItem] = []
    path = Path(path)

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            try:
                유효기간_시작, 유효기간_종료 = parse_date_range(row["유효기간"])
                갱신_시작, 갱신_종료 = parse_date_range(row["갱신신청기한"])

                제품명 = row["제품명"].replace("\n", " ").strip()

                item = DeviceItem(
                    제품명=제품명,
                    품목명=row["품목명"].strip(),
                    제조수입=row["제조/수입"].strip(),
                    품목허가번호=row["품목허가번호"].strip(),
                    허가일자=parse_date(row["허가일자"]),
                    최종변경일=parse_date(row["최종변경일"]),
                    유효기간_시작=유효기간_시작,
                    유효기간_종료=유효기간_종료,
                    갱신신청기한_시작=갱신_시작,
                    갱신신청기한_종료=갱신_종료,
                    알림발송일=edate(갱신_시작, -3),
                    알림발송일_1M=edate(갱신_시작, -1),
                    row_index=idx,
                )
                items.append(item)
            except Exception as e:
                logger.warning("의료기기 행 %d 파싱 실패: %s", idx, e)

    logger.info("의료기기 %d건 로드 완료 (경로: %s)", len(items), path)
    return items


def load_all(
    medicine_path: str | Path,
    device_path: str | Path,
) -> tuple[list[MedicineItem], list[DeviceItem]]:
    """의약품 + 의료기기 전체 로드."""
    medicines = load_medicine_csv(medicine_path)
    devices = load_device_csv(device_path)
    return medicines, devices
