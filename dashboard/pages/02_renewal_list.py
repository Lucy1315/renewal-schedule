import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import pandas as pd
import streamlit as st

from config import load_config, get_file_paths, get_log_path
from loader import load_all
from send_log import read_send_history

st.header("갱신 대상 목록")

config = load_config(Path(__file__).resolve().parent.parent.parent / "config.yaml")
paths = get_file_paths(config)
base = Path(__file__).resolve().parent.parent.parent

medicines, devices = load_all(base / paths["medicine_csv"], base / paths["device_csv"])
log_path = base / get_log_path(config)
history = read_send_history(log_path) if log_path.exists() else []

today = date.today()

# 발송 완료된 대상월 세트
sent_set = {
    (r.category, r.target_year_month)
    for r in history
    if r.status == "SUCCESS"
}


# --- 데이터 조합 ---
rows = []
for item in medicines:
    ym = f"{item.갱신신청기한.year}-{item.갱신신청기한.month:02d}"
    d_day = (item.갱신신청기한 - today).days
    sent = ("의약품", ym) in sent_set
    rows.append({
        "구분": "의약품",
        "제품명/품목명": item.제품명,
        "허가번호": item.허가번호,
        "갱신신청기한": str(item.갱신신청기한),
        "D-day": d_day,
        "알림발송일": str(item.알림발송일),
        "발송상태": "발송완료" if sent else "미발송",
        "연도": item.갱신신청기한.year,
    })

for item in devices:
    ym = f"{item.갱신신청기한_시작.year}-{item.갱신신청기한_시작.month:02d}"
    d_day = (item.갱신신청기한_시작 - today).days
    sent = ("의료기기", ym) in sent_set
    rows.append({
        "구분": "의료기기",
        "제품명/품목명": item.품목명,
        "허가번호": item.품목허가번호,
        "갱신신청기한": f"{item.갱신신청기한_시작} ~ {item.갱신신청기한_종료}",
        "D-day": d_day,
        "알림발송일": str(item.알림발송일),
        "발송상태": "발송완료" if sent else "미발송",
        "연도": item.갱신신청기한_시작.year,
    })

df = pd.DataFrame(rows)

# --- 필터 ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    cat_filter = st.selectbox("카테고리", ["전체", "의약품", "의료기기"])
with col2:
    years = sorted(df["연도"].unique())
    year_filter = st.selectbox("연도", ["전체"] + [str(y) for y in years])
with col3:
    status_filter = st.selectbox("상태", ["전체", "발송완료", "미발송"])
with col4:
    search = st.text_input("검색 (제품명)")

# 필터 적용
mask = pd.Series([True] * len(df))
if cat_filter != "전체":
    mask &= df["구분"] == cat_filter
if year_filter != "전체":
    mask &= df["연도"] == int(year_filter)
if status_filter != "전체":
    mask &= df["발송상태"] == status_filter
if search:
    mask &= df["제품명/품목명"].str.contains(search, case=False, na=False)

df_filtered = df[mask].sort_values("D-day").reset_index(drop=True)


# --- D-day 색상 ---
def highlight_dday(val):
    if isinstance(val, int):
        if val < 30:
            return "background-color: #FFCDD2"  # 빨강
        elif val < 60:
            return "background-color: #FFE0B2"  # 주황
        elif val < 90:
            return "background-color: #FFF9C4"  # 노랑
    return ""


display_cols = ["구분", "제품명/품목명", "허가번호", "갱신신청기한", "D-day", "알림발송일", "발송상태"]
styled = df_filtered[display_cols].style.map(highlight_dday, subset=["D-day"])

st.dataframe(styled, width="stretch", height=600)
st.caption(f"총 {len(df_filtered)}건")
