from __future__ import annotations

from pathlib import Path
from string import Template

from models import AlertTarget, Category, DeviceItem, MedicineItem

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def build_email_subject(
    category: Category,
    target_year: int,
    target_month: int,
    alert_type: str = "3M",
) -> str:
    """메일 제목 생성."""
    cat = category.value
    type_label = "3개월 전" if alert_type == "3M" else "1개월 전"
    return f"[RPA] {cat} 품목 갱신 신청기한 알림 ({type_label} / 신청 기한 {target_year}년 {target_month:02d}월)"


def build_email_body(alert: AlertTarget) -> str:
    """HTML 메일 본문 생성."""
    template_path = TEMPLATE_DIR / "email_base.html"
    template_str = template_path.read_text(encoding="utf-8")

    if alert.category == Category.MEDICINE:
        table_html = _render_medicine_table(alert.items_with_highlight)
    else:
        table_html = _render_device_table(alert.items_with_highlight)

    return Template(template_str).safe_substitute(
        CATEGORY=alert.category.value,
        TARGET_YEAR=str(alert.target_year),
        TARGET_MONTH=f"{alert.target_month:02d}",
        TABLE_HTML=table_html,
    )


def _render_medicine_table(
    items_with_highlight: list[tuple[MedicineItem, bool]],
) -> str:
    """의약품 HTML 테이블."""
    header_style = (
        "background-color: #4472C4; color: white; "
        "padding: 10px 12px; border: 1px solid #3565a5; text-align: center;"
    )
    cell_style = "padding: 8px 12px; border: 1px solid #ddd; text-align: center;"
    highlight_bg = "background-color: #FFFFCC;"

    rows = []
    for idx, (item, is_hl) in enumerate(items_with_highlight, start=1):
        row_style = highlight_bg if is_hl else ""
        rows.append(
            f'  <tr style="{row_style}">'
            f'<td style="{cell_style}">{idx}</td>'
            f'<td style="{cell_style} text-align: left;">{item.제품명}</td>'
            f'<td style="{cell_style}">{item.허가일}</td>'
            f'<td style="{cell_style}">{item.품목유효기간}</td>'
            f'<td style="{cell_style}">{item.갱신신청기한}</td>'
            f"</tr>"
        )

    return (
        '<table style="border-collapse: collapse; width: 100%; margin: 16px 0;">\n'
        f'  <tr><th style="{header_style}">No</th>'
        f'<th style="{header_style}">제품명</th>'
        f'<th style="{header_style}">허가일</th>'
        f'<th style="{header_style}">품목유효기간</th>'
        f'<th style="{header_style}">갱신신청기한</th></tr>\n'
        + "\n".join(rows)
        + "\n</table>"
    )


def _render_device_table(
    items_with_highlight: list[tuple[DeviceItem, bool]],
) -> str:
    """의료기기 HTML 테이블."""
    header_style = (
        "background-color: #4472C4; color: white; "
        "padding: 10px 12px; border: 1px solid #3565a5; text-align: center;"
    )
    cell_style = "padding: 8px 12px; border: 1px solid #ddd; text-align: center;"
    highlight_bg = "background-color: #FFFFCC;"

    rows = []
    for idx, (item, is_hl) in enumerate(items_with_highlight, start=1):
        row_style = highlight_bg if is_hl else ""
        유효기간 = f"{item.유효기간_시작} ~ {item.유효기간_종료}"
        갱신기한 = f"{item.갱신신청기한_시작} ~ {item.갱신신청기한_종료}"
        rows.append(
            f'  <tr style="{row_style}">'
            f'<td style="{cell_style}">{idx}</td>'
            f'<td style="{cell_style} text-align: left;">{item.품목명}</td>'
            f'<td style="{cell_style}">{item.품목허가번호}</td>'
            f'<td style="{cell_style}">{item.허가일자}</td>'
            f'<td style="{cell_style} font-size: 12px;">{유효기간}</td>'
            f'<td style="{cell_style} font-size: 12px;">{갱신기한}</td>'
            f"</tr>"
        )

    return (
        '<table style="border-collapse: collapse; width: 100%; margin: 16px 0;">\n'
        f'  <tr><th style="{header_style}">No</th>'
        f'<th style="{header_style}">품목명</th>'
        f'<th style="{header_style}">품목허가번호</th>'
        f'<th style="{header_style}">허가일자</th>'
        f'<th style="{header_style}">유효기간</th>'
        f'<th style="{header_style}">갱신신청기한</th></tr>\n'
        + "\n".join(rows)
        + "\n</table>"
    )
