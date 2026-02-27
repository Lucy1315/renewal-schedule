from __future__ import annotations

import os
from pathlib import Path

import yaml


def load_config(path: str | Path = "config.yaml") -> dict:
    """YAML 설정 파일 로드."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_smtp_config(config: dict) -> dict:
    """SMTP 설정 + 환경변수에서 비밀번호 결합."""
    smtp = dict(config["smtp"])
    smtp["password"] = os.environ.get("SMTP_PASSWORD", "")
    smtp.setdefault("username", smtp["sender"])
    return smtp


def get_recipients(config: dict) -> dict:
    """{'to': [...], 'cc': [...], 'bcc': [...]} 반환."""
    r = config.get("recipients", {})
    return {
        "to": r.get("to", []),
        "cc": r.get("cc", []),
        "bcc": r.get("bcc", []),
    }


def get_file_paths(config: dict) -> dict:
    """데이터 파일 경로 반환."""
    return {
        "medicine_csv": config["data"]["medicine_csv"],
        "device_csv": config["data"]["device_csv"],
    }


def get_log_path(config: dict) -> str:
    """발송 이력 로그 경로 반환."""
    return config["log"]["send_history"]


def get_retry_config(config: dict) -> dict:
    """재시도 설정 반환."""
    r = config.get("retry", {})
    return {
        "max_attempts": r.get("max_attempts", 3),
        "backoff_seconds": r.get("backoff_seconds", [1, 3, 9]),
    }
