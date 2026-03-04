import sys
from datetime import date, timedelta
from pathlib import Path

# src 모듈 import 경로 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import streamlit as st

from config import load_config, get_file_paths, get_log_path
from loader import load_all
from send_log import read_send_history

st.set_page_config(
    page_title="품목갱신 알림 대시보드",
    page_icon="📋",
    layout="wide",
)

st.title("품목갱신 알림 대시보드")

config = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
paths = get_file_paths(config)
base = Path(__file__).resolve().parent.parent

medicines, devices = load_all(base / paths["medicine_csv"], base / paths["device_csv"])
log_path = base / get_log_path(config)
history = read_send_history(log_path) if log_path.exists() else []

today = date.today()

# ================================================================
# 6개월 이내 신청 마감 현황
# ================================================================
cutoff_6m = today + timedelta(days=180)

upcoming_med = [i for i in medicines if today <= i.갱신신청기한 <= cutoff_6m]
upcoming_dev = [i for i in devices if today <= i.갱신신청기한_시작 <= cutoff_6m]

col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 관리 품목", f"{len(medicines) + len(devices)}건",
            f"의약품 {len(medicines)} / 의료기기 {len(devices)}")
col2.metric("6개월 이내 마감", f"{len(upcoming_med) + len(upcoming_dev)}건",
            f"의약품 {len(upcoming_med)} / 의료기기 {len(upcoming_dev)}")
col3.metric("3개월 이내 마감",
            f"{sum(1 for i in medicines if today <= i.갱신신청기한 <= today + timedelta(days=90)) + sum(1 for i in devices if today <= i.갱신신청기한_시작 <= today + timedelta(days=90))}건")
col4.metric("1개월 이내 마감",
            f"{sum(1 for i in medicines if today <= i.갱신신청기한 <= today + timedelta(days=30)) + sum(1 for i in devices if today <= i.갱신신청기한_시작 <= today + timedelta(days=30))}건")

# --- 6개월 이내 마감 품목 요약 테이블 ---
if upcoming_med or upcoming_dev:
    upcoming_rows = []
    for i in upcoming_med:
        upcoming_rows.append({
            "구분": "의약품",
            "제품명/품목명": i.제품명,
            "갱신신청기한": str(i.갱신신청기한),
            "D-day": (i.갱신신청기한 - today).days,
        })
    for i in upcoming_dev:
        upcoming_rows.append({
            "구분": "의료기기",
            "제품명/품목명": i.품목명,
            "갱신신청기한": f"{i.갱신신청기한_시작} ~ {i.갱신신청기한_종료}",
            "D-day": (i.갱신신청기한_시작 - today).days,
        })
    df_upcoming = pd.DataFrame(upcoming_rows).sort_values("D-day").reset_index(drop=True)

    def _urgency_color(val):
        if isinstance(val, int):
            if val < 30:
                return "background-color: #FFCDD2; font-weight: bold;"
            elif val < 90:
                return "background-color: #FFE0B2;"
            elif val < 180:
                return "background-color: #FFF9C4;"
        return ""

    st.dataframe(
        df_upcoming.style.map(_urgency_color, subset=["D-day"]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("6개월 이내 마감 품목이 없습니다.")

st.divider()

# ================================================================
# 갱신 대상 목록 (전체)
# ================================================================
st.header("갱신 대상 목록")

# 발송 완료된 대상월 세트 (category, target_year_month, alert_type)
sent_set = {
    (r.category, r.target_year_month, r.alert_type)
    for r in history
    if r.status == "SUCCESS"
}


def _med_send_status(ym, cat="의약품"):
    s3 = (cat, ym, "3M") in sent_set
    s1 = (cat, ym, "1M") in sent_set
    if s3 and s1:
        return "발송완료(3M+1M)"
    elif s3:
        return "발송완료(3M)"
    elif s1:
        return "발송완료(1M)"
    return "미발송"


# --- 데이터 조합 ---
med_rows = []
for item in medicines:
    ym = f"{item.갱신신청기한.year}-{item.갱신신청기한.month:02d}"
    d_day = (item.갱신신청기한 - today).days
    med_rows.append({
        "제품명": item.제품명,
        "허가번호": item.허가번호,
        "허가일": str(item.허가일),
        "품목유효기간": str(item.품목유효기간),
        "갱신신청기한": str(item.갱신신청기한),
        "D-day": d_day,
        "알림(3M)": str(item.알림발송일),
        "알림(1M)": str(item.알림발송일_1M),
        "전문/일반": item.전문일반,
        "품목분류": item.품목분류,
        "유효기간": item.유효기간,
        "관계부처": item.관계부처,
        "발송상태": _med_send_status(ym),
        "연도": item.갱신신청기한.year,
    })

dev_rows = []
for item in devices:
    ym = f"{item.갱신신청기한_시작.year}-{item.갱신신청기한_시작.month:02d}"
    d_day = (item.갱신신청기한_시작 - today).days
    dev_rows.append({
        "품목명": item.품목명,
        "제품명": item.제품명,
        "품목허가번호": item.품목허가번호,
        "허가일자": str(item.허가일자),
        "유효기간": f"{item.유효기간_시작} ~ {item.유효기간_종료}",
        "갱신신청기한": f"{item.갱신신청기한_시작} ~ {item.갱신신청기한_종료}",
        "D-day": d_day,
        "알림(3M)": str(item.알림발송일),
        "알림(1M)": str(item.알림발송일_1M),
        "발송상태": _med_send_status(ym, "의료기기"),
        "연도": item.갱신신청기한_시작.year,
    })

# 전체 (공통 컬럼) 데이터프레임
all_rows = []
for item in medicines:
    ym = f"{item.갱신신청기한.year}-{item.갱신신청기한.month:02d}"
    d_day = (item.갱신신청기한 - today).days
    all_rows.append({
        "구분": "의약품",
        "제품명/품목명": item.제품명,
        "허가번호": item.허가번호,
        "갱신신청기한": str(item.갱신신청기한),
        "D-day": d_day,
        "알림(3M)": str(item.알림발송일),
        "알림(1M)": str(item.알림발송일_1M),
        "발송상태": _med_send_status(ym),
        "연도": item.갱신신청기한.year,
    })
for item in devices:
    ym = f"{item.갱신신청기한_시작.year}-{item.갱신신청기한_시작.month:02d}"
    d_day = (item.갱신신청기한_시작 - today).days
    all_rows.append({
        "구분": "의료기기",
        "제품명/품목명": item.품목명,
        "허가번호": item.품목허가번호,
        "갱신신청기한": f"{item.갱신신청기한_시작} ~ {item.갱신신청기한_종료}",
        "D-day": d_day,
        "알림(3M)": str(item.알림발송일),
        "알림(1M)": str(item.알림발송일_1M),
        "발송상태": _med_send_status(ym, "의료기기"),
        "연도": item.갱신신청기한_시작.year,
    })

df_all = pd.DataFrame(all_rows)
df_med = pd.DataFrame(med_rows)
df_dev = pd.DataFrame(dev_rows)

# --- 필터 ---
col1, col2, col3 = st.columns(3)
with col1:
    years = sorted(set(df_all["연도"].unique()))
    year_filter = st.selectbox("연도", ["전체"] + [str(y) for y in years])
with col2:
    status_filter = st.selectbox("상태", ["전체", "발송완료", "미발송"])
with col3:
    search = st.text_input("검색 (제품명)")


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


def apply_filter(df, name_col="제품명/품목명"):
    mask = pd.Series([True] * len(df))
    if year_filter != "전체":
        mask &= df["연도"] == int(year_filter)
    if status_filter == "발송완료":
        mask &= df["발송상태"].str.startswith("발송완료")
    elif status_filter == "미발송":
        mask &= df["발송상태"] == "미발송"
    if search:
        mask &= df[name_col].str.contains(search, case=False, na=False)
    return df[mask].sort_values("D-day").reset_index(drop=True)


# --- 탭 ---
tab_all, tab_med, tab_dev = st.tabs(["전체", "의약품", "의료기기"])

with tab_all:
    filtered = apply_filter(df_all)
    cols = ["구분", "제품명/품목명", "허가번호", "갱신신청기한", "D-day", "알림(3M)", "알림(1M)", "발송상태"]
    styled = filtered[cols].style.map(highlight_dday, subset=["D-day"])
    st.dataframe(styled, use_container_width=True, height=600)
    st.caption(f"총 {len(filtered)}건")

with tab_med:
    filtered = apply_filter(df_med, name_col="제품명")
    cols = ["제품명", "허가번호", "허가일", "품목유효기간", "갱신신청기한", "D-day",
            "알림(3M)", "알림(1M)", "전문/일반", "품목분류", "유효기간", "관계부처", "발송상태"]
    styled = filtered[cols].style.map(highlight_dday, subset=["D-day"])
    st.dataframe(styled, use_container_width=True, height=600)
    st.caption(f"의약품 총 {len(filtered)}건")

with tab_dev:
    filtered = apply_filter(df_dev, name_col="품목명")
    cols = ["품목명", "제품명", "품목허가번호", "허가일자", "유효기간",
            "갱신신청기한", "D-day", "알림(3M)", "알림(1M)", "발송상태"]
    styled = filtered[cols].style.map(highlight_dday, subset=["D-day"])
    st.dataframe(styled, use_container_width=True, height=600)
    st.caption(f"의료기기 총 {len(filtered)}건")
