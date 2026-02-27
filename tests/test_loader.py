from datetime import date
from pathlib import Path

from loader import load_device_csv, load_medicine_csv, parse_date_range
from models import edate

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# --- edate 테스트 ---

class TestEdate:
    def test_normal(self):
        # 2026-08-19 - 3개월 = 2026-05-19
        assert edate(date(2026, 8, 19), -3) == date(2026, 5, 19)

    def test_month_end(self):
        # 2026-05-31 - 3개월 = 2026-02-28 (2월은 28일까지)
        assert edate(date(2026, 5, 31), -3) == date(2026, 2, 28)

    def test_leap_year(self):
        # 2028-05-29 - 3개월 = 2028-02-29 (윤년)
        assert edate(date(2028, 5, 29), -3) == date(2028, 2, 29)

    def test_year_cross(self):
        # 2027-01-12 - 3개월 = 2026-10-12
        assert edate(date(2027, 1, 12), -3) == date(2026, 10, 12)

    def test_positive_months(self):
        # 2026-01-15 + 3개월 = 2026-04-15
        assert edate(date(2026, 1, 15), 3) == date(2026, 4, 15)


# --- 날짜 범위 파싱 ---

class TestParseDateRange:
    def test_normal(self):
        start, end = parse_date_range("2026-02-26 ~ 2026-05-27")
        assert start == date(2026, 2, 26)
        assert end == date(2026, 5, 27)

    def test_with_extra_spaces(self):
        start, end = parse_date_range("2025-08-04 ~ 2025-11-02")
        assert start == date(2025, 8, 4)
        assert end == date(2025, 11, 2)


# --- 의약품 CSV 로딩 ---

class TestLoadMedicineCsv:
    def test_count(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        assert len(items) == 26  # 앤지덤패취, 써지가드거즈 삭제 후

    def test_first_item(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        first = items[0]
        assert "팔제론주" in first.제품명
        assert first.갱신신청기한 == date(2026, 8, 19)
        assert first.알림발송일 == date(2026, 5, 19)  # 3M
        assert first.알림발송일_1M == date(2026, 7, 19)  # 1M

    def test_alert_date_calculation(self):
        """모든 의약품의 알림발송일 = edate(갱신신청기한, -3), 알림발송일_1M = edate(갱신신청기한, -1) 확인."""
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        for item in items:
            expected_3m = edate(item.갱신신청기한, -3)
            assert item.알림발송일 == expected_3m, (
                f"{item.제품명}: 알림발송일 {item.알림발송일} != 예상 {expected_3m}"
            )
            expected_1m = edate(item.갱신신청기한, -1)
            assert item.알림발송일_1M == expected_1m, (
                f"{item.제품명}: 알림발송일_1M {item.알림발송일_1M} != 예상 {expected_1m}"
            )

    def test_row_index(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        assert items[0].row_index == 1
        assert items[-1].row_index == 26


# --- 의료기기 CSV 로딩 ---

class TestLoadDeviceCsv:
    def test_count(self):
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        assert len(items) == 31

    def test_date_range_parsed(self):
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        # 라풀렌: 갱신신청기한 2026-02-26 ~ 2026-05-27
        라풀렌 = [i for i in items if "라풀렌" in i.제품명][0]
        assert 라풀렌.갱신신청기한_시작 == date(2026, 2, 26)
        assert 라풀렌.갱신신청기한_종료 == date(2026, 5, 27)

    def test_alert_date_3m(self):
        """의료기기 알림발송일(3M) = edate(갱신신청기한_시작, -3)."""
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        라풀렌 = [i for i in items if "라풀렌" in i.제품명][0]
        # 시작일 2026-02-26 - 3M = 2025-11-26
        assert 라풀렌.알림발송일 == date(2025, 11, 26)

    def test_alert_date_1m(self):
        """의료기기 알림발송일_1M = edate(갱신신청기한_시작, -1)."""
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        라풀렌 = [i for i in items if "라풀렌" in i.제품명][0]
        # 시작일 2026-02-26 - 1M = 2026-01-26
        assert 라풀렌.알림발송일_1M == date(2026, 1, 26)

    def test_all_alert_dates_edate(self):
        """모든 의료기기의 알림발송일 = edate(갱신신청기한_시작, -3) 확인."""
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        for item in items:
            expected_3m = edate(item.갱신신청기한_시작, -3)
            assert item.알림발송일 == expected_3m, (
                f"{item.품목명}: 알림발송일 {item.알림발송일} != 예상 {expected_3m}"
            )
            expected_1m = edate(item.갱신신청기한_시작, -1)
            assert item.알림발송일_1M == expected_1m, (
                f"{item.품목명}: 알림발송일_1M {item.알림발송일_1M} != 예상 {expected_1m}"
            )

    def test_multiline_product_name(self):
        """줄바꿈 포함 제품명이 공백으로 치환되는지 확인."""
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        for item in items:
            assert "\n" not in item.제품명, (
                f"제품명에 줄바꿈 포함: {repr(item.제품명)}"
            )
