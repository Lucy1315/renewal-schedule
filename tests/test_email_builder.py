from datetime import date
from pathlib import Path

from email_builder import build_email_body, build_email_subject
from loader import load_device_csv, load_medicine_csv
from models import Category
from rules import find_device_alerts, find_medicine_alerts

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestEmailSubject:
    def test_medicine_3m_format(self):
        subject = build_email_subject(Category.MEDICINE, 2026, 8, "3M")
        assert subject == "[RPA] 의약품 품목 갱신 신청기한 알림 (3개월 전 / 신청 기한 2026년 08월)"

    def test_medicine_1m_format(self):
        subject = build_email_subject(Category.MEDICINE, 2026, 8, "1M")
        assert subject == "[RPA] 의약품 품목 갱신 신청기한 알림 (1개월 전 / 신청 기한 2026년 08월)"

    def test_device_format(self):
        subject = build_email_subject(Category.DEVICE, 2026, 2, "3M")
        assert subject == "[RPA] 의료기기 품목 갱신 신청기한 알림 (3개월 전 / 신청 기한 2026년 02월)"


class TestEmailBody:
    def test_medicine_body_contains_table(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        alerts = find_medicine_alerts(items, date(2026, 5, 19))
        assert len(alerts) >= 1
        body = build_email_body(alerts[0])
        assert "<table" in body
        assert "팔제론주" in body

    def test_medicine_body_highlight(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        alerts = find_medicine_alerts(items, date(2026, 5, 19))
        body = build_email_body(alerts[0])
        assert "#FFFFCC" in body

    def test_medicine_table_columns(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        alerts = find_medicine_alerts(items, date(2026, 5, 19))
        body = build_email_body(alerts[0])
        assert "제품명" in body
        assert "허가일" in body
        assert "품목유효기간" in body
        assert "갱신신청기한" in body

    def test_device_body_contains_table(self):
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        # 라풀렌 3M: 2025-11-26
        alerts = find_device_alerts(items, date(2025, 11, 26))
        assert len(alerts) >= 1
        body = build_email_body(alerts[0])
        assert "<table" in body
        assert "라풀렌" in body or "조직수복용재료" in body

    def test_device_table_columns(self):
        items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")
        alerts = find_device_alerts(items, date(2025, 11, 26))
        body = build_email_body(alerts[0])
        assert "품목명" in body
        assert "품목허가번호" in body
        assert "허가일자" in body
        assert "유효기간" in body

    def test_body_contains_target_month_text(self):
        items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")
        alerts = find_medicine_alerts(items, date(2026, 5, 19))
        body = build_email_body(alerts[0])
        assert "2026년 08월" in body
