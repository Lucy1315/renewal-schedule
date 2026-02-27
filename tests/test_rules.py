from datetime import date
from pathlib import Path

from loader import load_device_csv, load_medicine_csv
from rules import find_device_alerts, find_medicine_alerts

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestMedicineAlerts:
    def setup_method(self):
        self.items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")

    def test_scenario1_3m_alert(self):
        """PRD 시나리오: 갱신신청기한=2026-08-19 → 2026-05-19에 3M '2026년 08월' 메일."""
        alerts = find_medicine_alerts(self.items, date(2026, 5, 19))
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.target_year == 2026
        assert alert.target_month == 8
        assert alert.alert_type == "3M"
        names = [i.제품명 for i, _ in alert.items_with_highlight]
        assert any("팔제론주" in n for n in names)

    def test_scenario1_1m_alert(self):
        """갱신신청기한=2026-08-19 → 2026-07-19에 1M '2026년 08월' 메일."""
        alerts = find_medicine_alerts(self.items, date(2026, 7, 19))
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.target_year == 2026
        assert alert.target_month == 8
        assert alert.alert_type == "1M"

    def test_no_alert_on_non_matching_date(self):
        """알림발송일이 아닌 날에는 빈 리스트 반환."""
        alerts = find_medicine_alerts(self.items, date(2026, 5, 20))
        assert alerts == []

    def test_target_month_includes_rest_of_year(self):
        """대상월 이후 동년 품목이 포함되는지 확인."""
        alerts = find_medicine_alerts(self.items, date(2026, 5, 19))
        assert len(alerts) >= 1
        alert = alerts[0]
        months = {i.갱신신청기한.month for i, _ in alert.items_with_highlight}
        assert 8 in months
        assert 11 in months or 12 in months

    def test_highlight_only_target_month(self):
        """대상월 품목만 is_highlight=True."""
        alerts = find_medicine_alerts(self.items, date(2026, 5, 19))
        alert = alerts[0]
        for item, is_highlight in alert.items_with_highlight:
            if item.갱신신청기한.month == 8 and item.갱신신청기한.year == 2026:
                assert is_highlight is True
            else:
                assert is_highlight is False

    def test_scenario2_december_includes_next_year(self):
        """PRD 시나리오: 대상월 12월이면 다음 연도 전체 포함."""
        alerts = find_medicine_alerts(self.items, date(2026, 9, 30))
        assert len(alerts) >= 1
        alert = [a for a in alerts if a.target_month == 12][0]
        years = {i.갱신신청기한.year for i, _ in alert.items_with_highlight}
        assert 2027 in years

    def test_december_next_year_not_highlighted(self):
        """12월 케이스에서 다음 연도 품목은 하이라이트 아님."""
        alerts = find_medicine_alerts(self.items, date(2026, 9, 30))
        alert = [a for a in alerts if a.target_month == 12][0]
        for item, is_highlight in alert.items_with_highlight:
            if item.갱신신청기한.year == 2027:
                assert is_highlight is False


class TestDeviceAlerts:
    def setup_method(self):
        self.items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")

    def test_3m_alert(self):
        """의료기기 3M 알림: edate(갱신신청기한_시작, -3) 날짜에 발생."""
        # 라풀렌: 갱신신청기한_시작=2026-02-26, 3M=2025-11-26
        alerts = find_device_alerts(self.items, date(2025, 11, 26))
        assert len(alerts) >= 1
        alert = [a for a in alerts if a.alert_type == "3M"][0]
        assert alert.target_year == 2026
        assert alert.target_month == 2
        names = [i.제품명 for i, _ in alert.items_with_highlight]
        assert any("라풀렌" in n for n in names)

    def test_1m_alert(self):
        """의료기기 1M 알림: edate(갱신신청기한_시작, -1) 날짜에 발생."""
        # 라풀렌: 갱신신청기한_시작=2026-02-26, 1M=2026-01-26
        alerts = find_device_alerts(self.items, date(2026, 1, 26))
        assert len(alerts) >= 1
        alert = [a for a in alerts if a.alert_type == "1M"][0]
        assert alert.target_year == 2026
        assert alert.target_month == 2

    def test_no_alert_wrong_date(self):
        alerts = find_device_alerts(self.items, date(2026, 2, 27))
        assert alerts == []

    def test_device_includes_rest_of_year(self):
        """대상월 이후 동년 품목 포함."""
        alerts = find_device_alerts(self.items, date(2025, 5, 4))
        assert len(alerts) >= 1
        alert = alerts[0]
        months = {i.갱신신청기한_시작.month for i, _ in alert.items_with_highlight}
        assert len(months) >= 1

    def test_sorted_by_deadline(self):
        """결과가 갱신신청기한 순으로 정렬되어 있는지 확인."""
        alerts = find_device_alerts(self.items, date(2025, 11, 26))
        if alerts:
            alert = alerts[0]
            dates = [i.갱신신청기한_시작 for i, _ in alert.items_with_highlight]
            assert dates == sorted(dates)
