"""배치 엔트리포인트. cron/Task Scheduler에서 호출."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from main import main  # noqa: E402

if __name__ == "__main__":
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser(description="품목갱신 알림 배치")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--date", type=str, help="YYYY-MM-DD")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None
    main(dry_run=args.dry_run, target_date=target)
