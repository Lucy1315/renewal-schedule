from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path

# src 디렉터리가 sys.path에 포함되도록 설정
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    get_file_paths,
    get_log_path,
    get_recipients,
    get_retry_config,
    get_smtp_config,
    load_config,
)
from email_builder import build_email_body, build_email_subject
from loader import load_all
from mailer import send_with_retry
from models import AlertTarget, Category, SendRecord
from rules import find_device_alerts, find_medicine_alerts
from send_log import append_send_record, has_been_sent, init_log_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _process_alert(
    alert: AlertTarget,
    config: dict,
    log_path: str,
    dry_run: bool,
) -> None:
    """단일 카테고리 알림 처리."""
    category_name = alert.category.value
    target_ym = f"{alert.target_year}-{alert.target_month:02d}"
    alert_type = alert.alert_type  # "3M" or "1M"

    # 멱등성 체크
    if has_been_sent(log_path, category_name, target_ym, alert_type):
        logger.info("[%s/%s] %s 이미 발송됨 → skip", category_name, alert_type, target_ym)
        return

    # 이메일 생성
    subject = build_email_subject(alert.category, alert.target_year, alert.target_month, alert_type)
    body = build_email_body(alert)
    item_count = len(alert.items_with_highlight)

    logger.info("[%s/%s] 대상: %s (%d건)", category_name, alert_type, target_ym, item_count)

    if dry_run:
        logger.info("[DRY-RUN] 메일 제목: %s", subject)
        logger.info("[DRY-RUN] 대상 품목 %d건:", item_count)
        for item, is_hl in alert.items_with_highlight:
            name = getattr(item, "제품명", getattr(item, "품목명", ""))
            mark = "★" if is_hl else " "
            logger.info("  %s %s", mark, name)
        # dry-run 시 HTML을 파일로 저장하여 확인 가능하게
        preview_path = Path(f"logs/preview_{category_name}_{target_ym}_{alert_type}.html")
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text(body, encoding="utf-8")
        logger.info("[DRY-RUN] HTML 미리보기: %s", preview_path)
        return

    # 실제 발송
    smtp_config = get_smtp_config(config)
    recipients = get_recipients(config)
    retry_config = get_retry_config(config)

    success, error_msg = send_with_retry(
        smtp_config=smtp_config,
        recipients=recipients,
        subject=subject,
        html_body=body,
        max_attempts=retry_config["max_attempts"],
        backoff_seconds=retry_config["backoff_seconds"],
    )

    # 이력 기록
    record = SendRecord(
        run_datetime=datetime.now().isoformat(timespec="seconds"),
        category=category_name,
        target_year_month=target_ym,
        alert_type=alert_type,
        item_count=item_count,
        status="SUCCESS" if success else "FAIL",
        error_message=error_msg,
        recipients=", ".join(recipients["to"]),
    )
    append_send_record(log_path, record)

    if success:
        logger.info("[%s/%s] %s 발송 성공", category_name, alert_type, target_ym)
    else:
        logger.error("[%s/%s] %s 발송 실패: %s", category_name, alert_type, target_ym, error_msg)


def main(dry_run: bool = False, target_date: date | None = None) -> None:
    """배치 실행 메인."""
    today = target_date or date.today()
    logger.info("=== 품목갱신 알림 배치 시작 (날짜: %s, dry_run: %s) ===", today, dry_run)

    config = load_config()
    paths = get_file_paths(config)
    log_path = get_log_path(config)
    init_log_file(log_path)

    # 데이터 로드
    medicines, devices = load_all(paths["medicine_csv"], paths["device_csv"])

    # 의약품 알림 (3M + 1M)
    med_alerts = find_medicine_alerts(medicines, today)
    if med_alerts:
        for alert in med_alerts:
            _process_alert(alert, config, log_path, dry_run)
    else:
        logger.info("[의약품] 오늘(%s) 발송 대상 없음", today)

    # 의료기기 알림 (3M + 1M)
    dev_alerts = find_device_alerts(devices, today)
    if dev_alerts:
        for alert in dev_alerts:
            _process_alert(alert, config, log_path, dry_run)
    else:
        logger.info("[의료기기] 오늘(%s) 발송 대상 없음", today)

    logger.info("=== 배치 완료 ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="품목갱신 알림 배치")
    parser.add_argument("--dry-run", action="store_true", help="실제 발송 없이 대상 확인")
    parser.add_argument("--date", type=str, help="실행일 오버라이드 (YYYY-MM-DD)")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None
    main(dry_run=args.dry_run, target_date=target)
