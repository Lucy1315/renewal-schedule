import tempfile
from pathlib import Path

from models import SendRecord
from send_log import append_send_record, has_been_sent, init_log_file, read_send_history


class TestSendLog:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.log_path = Path(self.tmp.name)
        self.tmp.close()
        self.log_path.unlink()  # 파일 없는 상태에서 시작

    def test_init_creates_header(self):
        init_log_file(self.log_path)
        assert self.log_path.exists()
        content = self.log_path.read_text(encoding="utf-8")
        assert "run_datetime" in content
        assert "alert_type" in content

    def test_append_and_read(self):
        record = SendRecord(
            run_datetime="2026-02-27T09:00:00",
            category="의료기기",
            target_year_month="2026-02",
            alert_type="3M",
            item_count=1,
            status="SUCCESS",
            error_message="",
            recipients="test@example.com",
        )
        append_send_record(self.log_path, record)
        records = read_send_history(self.log_path)
        assert len(records) == 1
        assert records[0].category == "의료기기"
        assert records[0].target_year_month == "2026-02"
        assert records[0].alert_type == "3M"
        assert records[0].status == "SUCCESS"

    def test_has_been_sent_true(self):
        record = SendRecord(
            run_datetime="2026-02-27T09:00:00",
            category="의약품",
            target_year_month="2026-08",
            alert_type="3M",
            item_count=3,
            status="SUCCESS",
            error_message="",
            recipients="test@example.com",
        )
        append_send_record(self.log_path, record)
        assert has_been_sent(self.log_path, "의약품", "2026-08", "3M") is True

    def test_has_been_sent_false(self):
        init_log_file(self.log_path)
        assert has_been_sent(self.log_path, "의약품", "2026-08", "3M") is False

    def test_has_been_sent_fail_only(self):
        """FAIL 기록만 있으면 재발송 허용."""
        record = SendRecord(
            run_datetime="2026-02-27T09:00:00",
            category="의약품",
            target_year_month="2026-08",
            alert_type="3M",
            item_count=3,
            status="FAIL",
            error_message="SMTP timeout",
            recipients="test@example.com",
        )
        append_send_record(self.log_path, record)
        assert has_been_sent(self.log_path, "의약품", "2026-08", "3M") is False

    def test_different_category_independent(self):
        """다른 카테고리는 독립적."""
        record = SendRecord(
            run_datetime="2026-02-27T09:00:00",
            category="의약품",
            target_year_month="2026-08",
            alert_type="3M",
            item_count=3,
            status="SUCCESS",
            error_message="",
            recipients="test@example.com",
        )
        append_send_record(self.log_path, record)
        assert has_been_sent(self.log_path, "의료기기", "2026-08", "3M") is False

    def test_different_alert_type_independent(self):
        """3M 발송 완료해도 1M은 독립적으로 발송 가능."""
        record = SendRecord(
            run_datetime="2026-02-27T09:00:00",
            category="의약품",
            target_year_month="2026-08",
            alert_type="3M",
            item_count=3,
            status="SUCCESS",
            error_message="",
            recipients="test@example.com",
        )
        append_send_record(self.log_path, record)
        assert has_been_sent(self.log_path, "의약품", "2026-08", "3M") is True
        assert has_been_sent(self.log_path, "의약품", "2026-08", "1M") is False
