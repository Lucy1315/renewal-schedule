from __future__ import annotations

from datetime import date

from models import AlertTarget, Category, DeviceItem, MedicineItem


def find_medicine_alerts(
    items: list[MedicineItem],
    today: date,
) -> list[AlertTarget]:
    """오늘 발송할 의약품 알림 대상 산출 (3개월 전 + 1개월 전).

    알림발송일(3M) 또는 알림발송일_1M == today인 품목이 있으면 AlertTarget을 반환한다.
    메일 표에는 동일 연도 대상월 이상(>=) 전체 품목을 포함하며,
    대상월이 12월이면 다음 연도 전체 품목도 추가한다.
    """
    alerts: list[AlertTarget] = []

    # 3개월 전 알림
    triggered_3m = [i for i in items if i.알림발송일 == today]
    if triggered_3m:
        target_year = triggered_3m[0].갱신신청기한.year
        target_month = triggered_3m[0].갱신신청기한.month
        items_with_highlight = _collect_medicine_table_items(
            items, target_year, target_month
        )
        alerts.append(AlertTarget(
            category=Category.MEDICINE,
            target_year=target_year,
            target_month=target_month,
            alert_type="3M",
            items_with_highlight=items_with_highlight,
        ))

    # 1개월 전 알림
    triggered_1m = [i for i in items if i.알림발송일_1M == today]
    if triggered_1m:
        target_year = triggered_1m[0].갱신신청기한.year
        target_month = triggered_1m[0].갱신신청기한.month
        items_with_highlight = _collect_medicine_table_items(
            items, target_year, target_month
        )
        alerts.append(AlertTarget(
            category=Category.MEDICINE,
            target_year=target_year,
            target_month=target_month,
            alert_type="1M",
            items_with_highlight=items_with_highlight,
        ))

    return alerts


def find_device_alerts(
    items: list[DeviceItem],
    today: date,
) -> list[AlertTarget]:
    """오늘 발송할 의료기기 알림 대상 산출 (3개월 전 + 1개월 전)."""
    alerts: list[AlertTarget] = []

    # 3개월 전 알림
    triggered_3m = [i for i in items if i.알림발송일 == today]
    if triggered_3m:
        target_year = triggered_3m[0].갱신신청기한_시작.year
        target_month = triggered_3m[0].갱신신청기한_시작.month
        items_with_highlight = _collect_device_table_items(
            items, target_year, target_month
        )
        alerts.append(AlertTarget(
            category=Category.DEVICE,
            target_year=target_year,
            target_month=target_month,
            alert_type="3M",
            items_with_highlight=items_with_highlight,
        ))

    # 1개월 전 알림
    triggered_1m = [i for i in items if i.알림발송일_1M == today]
    if triggered_1m:
        target_year = triggered_1m[0].갱신신청기한_시작.year
        target_month = triggered_1m[0].갱신신청기한_시작.month
        items_with_highlight = _collect_device_table_items(
            items, target_year, target_month
        )
        alerts.append(AlertTarget(
            category=Category.DEVICE,
            target_year=target_year,
            target_month=target_month,
            alert_type="1M",
            items_with_highlight=items_with_highlight,
        ))

    return alerts


def _collect_medicine_table_items(
    items: list[MedicineItem],
    target_year: int,
    target_month: int,
) -> list[tuple[MedicineItem, bool]]:
    """대상월 이상 품목 수집. (item, is_highlight) 튜플 리스트."""
    result: list[tuple[MedicineItem, bool]] = []

    for item in items:
        y = item.갱신신청기한.year
        m = item.갱신신청기한.month

        # 동일 연도, 대상월 이상
        if y == target_year and m >= target_month:
            is_highlight = m == target_month
            result.append((item, is_highlight))
        # 대상월이 12월이면 다음 연도 전체
        elif target_month == 12 and y == target_year + 1:
            result.append((item, False))

    # 갱신신청기한 순으로 정렬
    result.sort(key=lambda x: x[0].갱신신청기한)
    return result


def _collect_device_table_items(
    items: list[DeviceItem],
    target_year: int,
    target_month: int,
) -> list[tuple[DeviceItem, bool]]:
    """대상월 이상 의료기기 품목 수집."""
    result: list[tuple[DeviceItem, bool]] = []

    for item in items:
        y = item.갱신신청기한_시작.year
        m = item.갱신신청기한_시작.month

        if y == target_year and m >= target_month:
            is_highlight = m == target_month
            result.append((item, is_highlight))
        elif target_month == 12 and y == target_year + 1:
            result.append((item, False))

    result.sort(key=lambda x: x[0].갱신신청기한_시작)
    return result
