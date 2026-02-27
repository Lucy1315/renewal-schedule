from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from enum import Enum


class Category(Enum):
    MEDICINE = "의약품"
    DEVICE = "의료기기"


@dataclass
class MedicineItem:
    """의약품 갱신 품목"""
    제품명: str
    허가일: date
    품목유효기간: date
    갱신신청기한: date
    알림발송일: date          # edate(갱신신청기한, -3)
    업종: str
    제조수입: str
    허가번호: str
    품목기준코드: str
    전문일반: str
    품목분류: str
    허가신고: str
    유효기간: str             # 텍스트 (예: "제조일로부터 36 개월")
    관계부처: str
    row_index: int            # 원본 행 번호 (1-based, 헤더 제외)


@dataclass
class DeviceItem:
    """의료기기 갱신 품목"""
    제품명: str
    품목명: str
    제조수입: str
    품목허가번호: str
    허가일자: date
    최종변경일: date
    유효기간_시작: date
    유효기간_종료: date
    갱신신청기한_시작: date
    갱신신청기한_종료: date
    알림발송일: date          # 갱신신청기한_시작일이 속한 달의 1일
    row_index: int


@dataclass
class AlertTarget:
    """발송 대상 그룹"""
    category: Category
    target_year: int
    target_month: int
    items_with_highlight: list[tuple]  # (MedicineItem|DeviceItem, is_highlight: bool)


@dataclass
class SendRecord:
    """발송 이력 레코드"""
    run_datetime: str         # ISO format
    category: str             # "의약품" | "의료기기"
    target_year_month: str    # "YYYY-MM"
    item_count: int
    status: str               # "SUCCESS" | "FAIL"
    error_message: str
    recipients: str


def edate(base: date, months: int) -> date:
    """Excel EDATE 함수 구현. base에서 months만큼 이동 (음수=과거)."""
    total_months = base.month + months
    new_year = base.year + (total_months - 1) // 12
    new_month = (total_months - 1) % 12 + 1
    max_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(base.day, max_day)
    return date(new_year, new_month, new_day)
