from datetime import date
from pathlib import Path

from loader import load_device_csv, load_medicine_csv
from rules import find_device_alerts, find_medicine_alerts

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestMedicineAlerts:
    def setup_method(self):
        self.items = load_medicine_csv(DATA_DIR / "의약품갱신일정.csv")

    def test_scenario1_prd(self):
        """PRD 시나리오: 갱신신청기한=2026-08-19 → 2026-05-19에 '2026년 08월' 메일."""
        alert = find_medicine_alerts(self.items, date(2026, 5, 19))
        assert alert is not None
        assert alert.target_year == 2026
        assert alert.target_month == 8
        # 팔제론주가 포함되어 있어야 함
        names = [i.제품명 for i, _ in alert.items_with_highlight]
        assert any("팔제론주" in n for n in names)

    def test_no_alert_on_non_matching_date(self):
        """알림발송일이 아닌 날에는 None 반환."""
        alert = find_medicine_alerts(self.items, date(2026, 5, 20))
        assert alert is None

    def test_target_month_includes_rest_of_year(self):
        """대상월 이후 동년 품목이 포함되는지 확인."""
        alert = find_medicine_alerts(self.items, date(2026, 5, 19))
        assert alert is not None
        # 대상월=8월, 이후(11월, 12월) 품목도 포함
        months = {i.갱신신청기한.month for i, _ in alert.items_with_highlight}
        assert 8 in months
        assert 11 in months or 12 in months

    def test_highlight_only_target_month(self):
        """대상월 품목만 is_highlight=True."""
        alert = find_medicine_alerts(self.items, date(2026, 5, 19))
        assert alert is not None
        for item, is_highlight in alert.items_with_highlight:
            if item.갱신신청기한.month == 8 and item.갱신신청기한.year == 2026:
                assert is_highlight is True
            else:
                assert is_highlight is False

    def test_scenario2_december_includes_next_year(self):
        """PRD 시나리오: 대상월 12월이면 다음 연도 전체 포함."""
        alert = find_medicine_alerts(self.items, date(2026, 9, 30))
        assert alert is not None
        assert alert.target_month == 12
        # 다음 연도(2027) 품목이 포함되어야 함
        years = {i.갱신신청기한.year for i, _ in alert.items_with_highlight}
        assert 2027 in years

    def test_december_next_year_not_highlighted(self):
        """12월 케이스에서 다음 연도 품목은 하이라이트 아님."""
        alert = find_medicine_alerts(self.items, date(2026, 9, 30))
        assert alert is not None
        for item, is_highlight in alert.items_with_highlight:
            if item.갱신신청기한.year == 2027:
                assert is_highlight is False


class TestDeviceAlerts:
    def setup_method(self):
        self.items = load_device_csv(DATA_DIR / "의료기기갱신일정.csv")

    def test_scenario3_prd(self):
        """PRD 시나리오: 시작일=2026-02-26 → 2026-02-01에 '2026년 02월' 메일."""
        alert = find_device_alerts(self.items, date(2026, 2, 1))
        assert alert is not None
        assert alert.target_year == 2026
        assert alert.target_month == 2
        names = [i.제품명 for i, _ in alert.items_with_highlight]
        assert any("라풀렌" in n for n in names)

    def test_no_alert_wrong_date(self):
        alert = find_device_alerts(self.items, date(2026, 2, 27))
        assert alert is None

    def test_device_includes_rest_of_year(self):
        """대상월 이후 동년 품목 포함."""
        alert = find_device_alerts(self.items, date(2025, 8, 1))
        assert alert is not None
        months = {i.갱신신청기한_시작.month for i, _ in alert.items_with_highlight}
        # 8월 이후 품목도 있어야 함
        assert len(months) >= 1

    def test_sorted_by_deadline(self):
        """결과가 갱신신청기한 순으로 정렬되어 있는지 확인."""
        alert = find_device_alerts(self.items, date(2026, 2, 1))
        if alert:
            dates = [i.갱신신청기한_시작 for i, _ in alert.items_with_highlight]
            assert dates == sorted(dates)
