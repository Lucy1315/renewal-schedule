import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import pandas as pd
import streamlit as st

from config import load_config, get_file_paths, get_log_path
from loader import load_all
from rules import find_device_alerts, find_medicine_alerts
from send_log import read_send_history

st.header("발송 이력")

config = load_config(Path(__file__).resolve().parent.parent.parent / "config.yaml")
base = Path(__file__).resolve().parent.parent.parent
log_path = base / get_log_path(config)

history = read_send_history(log_path) if log_path.exists() else []

if not history:
    st.info("발송 이력이 없습니다.")
    st.stop()

# --- 필터 ---
col1, col2 = st.columns(2)
with col1:
    status_filter = st.selectbox("상태", ["전체", "SUCCESS", "FAIL"])
with col2:
    cat_filter = st.selectbox("카테고리", ["전체", "의약품", "의료기기"])

rows = []
for r in history:
    rows.append({
        "실행일시": r.run_datetime,
        "구분": r.category,
        "대상월": r.target_year_month,
        "건수": r.item_count,
        "상태": r.status,
        "에러": r.error_message,
        "수신자": r.recipients,
    })

df = pd.DataFrame(rows)

mask = pd.Series([True] * len(df))
if status_filter != "전체":
    mask &= df["상태"] == status_filter
if cat_filter != "전체":
    mask &= df["구분"] == cat_filter

df_filtered = df[mask].sort_values("실행일시", ascending=False).reset_index(drop=True)
st.dataframe(df_filtered, width="stretch")

# --- Drill-down ---
st.divider()
st.subheader("품목 상세 (Drill-down)")

target_months = df_filtered["대상월"].unique().tolist()
if target_months:
    selected_ym = st.selectbox("대상월 선택", target_months)
    selected_cat = df_filtered[df_filtered["대상월"] == selected_ym]["구분"].iloc[0]

    if selected_ym and selected_cat:
        paths = get_file_paths(config)
        medicines, devices = load_all(base / paths["medicine_csv"], base / paths["device_csv"])

        year, month = map(int, selected_ym.split("-"))

        if selected_cat == "의약품":
            items = [i for i in medicines
                     if i.갱신신청기한.year == year and i.갱신신청기한.month >= month]
            detail = [{"제품명": i.제품명, "갱신신청기한": str(i.갱신신청기한)} for i in items]
        else:
            items = [i for i in devices
                     if i.갱신신청기한_시작.year == year and i.갱신신청기한_시작.month >= month]
            detail = [{"품목명": i.품목명, "갱신신청기한": f"{i.갱신신청기한_시작} ~ {i.갱신신청기한_종료}"} for i in items]

        if detail:
            st.dataframe(pd.DataFrame(detail), width="stretch")
        else:
            st.info("해당 대상월의 품목이 없습니다.")
