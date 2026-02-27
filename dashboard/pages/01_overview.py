import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import pandas as pd
import streamlit as st

from config import load_config, get_file_paths, get_log_path
from loader import load_all
from send_log import read_send_history

st.header("개요 (Overview)")

# --- 데이터 로드 ---
config = load_config(Path(__file__).resolve().parent.parent.parent / "config.yaml")
paths = get_file_paths(config)
base = Path(__file__).resolve().parent.parent.parent

medicines, devices = load_all(base / paths["medicine_csv"], base / paths["device_csv"])
log_path = base / get_log_path(config)
history = read_send_history(log_path) if log_path.exists() else []

today = date.today()


# --- KPI 카드 ---
def count_by_deadline(items, days_ahead, get_deadline):
    cutoff = today + timedelta(days=days_ahead)
    return sum(1 for i in items if today <= get_deadline(i) <= cutoff)


def med_deadline(i):
    return i.갱신신청기한


def dev_deadline(i):
    return i.갱신신청기한_시작


# 이번 달 / 다음 달 알림 대상 (3M 또는 1M 알림이 이번달/다음달에 해당하는 건)
def _alert_in_month(item, yr, mo):
    return (
        (item.알림발송일.year == yr and item.알림발송일.month == mo)
        or (item.알림발송일_1M.year == yr and item.알림발송일_1M.month == mo)
    )

this_month_med = sum(1 for i in medicines if _alert_in_month(i, today.year, today.month))
this_month_dev = sum(1 for i in devices if _alert_in_month(i, today.year, today.month))

next_month = today.replace(day=1) + timedelta(days=32)
next_month = next_month.replace(day=1)
next_month_med = sum(1 for i in medicines if _alert_in_month(i, next_month.year, next_month.month))
next_month_dev = sum(1 for i in devices if _alert_in_month(i, next_month.year, next_month.month))

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("이번 달 대상", f"{this_month_med + this_month_dev}건",
            f"의약품 {this_month_med} / 의료기기 {this_month_dev}")
col2.metric("다음 달 대상", f"{next_month_med + next_month_dev}건",
            f"의약품 {next_month_med} / 의료기기 {next_month_dev}")
col3.metric("30일 이내",
            f"{count_by_deadline(medicines, 30, med_deadline) + count_by_deadline(devices, 30, dev_deadline)}건")
col4.metric("60일 이내",
            f"{count_by_deadline(medicines, 60, med_deadline) + count_by_deadline(devices, 60, dev_deadline)}건")
col5.metric("90일 이내",
            f"{count_by_deadline(medicines, 90, med_deadline) + count_by_deadline(devices, 90, dev_deadline)}건")

st.divider()

# --- 월별 갱신 건수 추이 차트 ---
st.subheader("월별 갱신 건수 추이")

chart_data = []
for item in medicines:
    chart_data.append({
        "연월": f"{item.갱신신청기한.year}-{item.갱신신청기한.month:02d}",
        "구분": "의약품",
        "건수": 1,
    })
for item in devices:
    chart_data.append({
        "연월": f"{item.갱신신청기한_시작.year}-{item.갱신신청기한_시작.month:02d}",
        "구분": "의료기기",
        "건수": 1,
    })

if chart_data:
    df_chart = pd.DataFrame(chart_data)
    df_pivot = df_chart.groupby(["연월", "구분"])["건수"].sum().reset_index()
    df_pivot_wide = df_pivot.pivot(index="연월", columns="구분", values="건수").fillna(0).sort_index()
    st.bar_chart(df_pivot_wide)

st.divider()

# --- 카테고리별 분포 ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("카테고리별 분포")
    total_med = len(medicines)
    total_dev = len(devices)
    total = total_med + total_dev
    df_cat = pd.DataFrame({
        "카테고리": ["의약품", "의료기기"],
        "건수": [total_med, total_dev],
    })
    st.dataframe(df_cat, hide_index=True, width="stretch")
    st.caption(f"전체 {total}건 (의약품 {total_med}건, 의료기기 {total_dev}건)")

with col_right:
    st.subheader("발송 상태 요약")
    sent_success = sum(1 for r in history if r.status == "SUCCESS")
    sent_fail = sum(1 for r in history if r.status == "FAIL")
    st.metric("발송 완료", f"{sent_success}건")
    st.metric("발송 실패", f"{sent_fail}건")
