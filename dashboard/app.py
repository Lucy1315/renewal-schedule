import sys
from datetime import date, timedelta
from pathlib import Path

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

# ================================================================
# Custom CSS
# ================================================================
st.markdown("""
<style>
/* 카드 컨테이너 */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-top: 4px solid #ddd;
    text-align: center;
}
.metric-card.urgent { border-top-color: #EF4444; }
.metric-card.warning { border-top-color: #F59E0B; }
.metric-card.info { border-top-color: #3B82F6; }

.metric-card .label {
    font-size: 13px;
    color: #6B7280;
    margin-bottom: 4px;
    font-weight: 500;
}
.metric-card .value {
    font-size: 36px;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
}
.metric-card .sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}

/* D-day 뱃지 */
.dday-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}
.dday-urgent { background: #FEE2E2; color: #DC2626; }
.dday-warn { background: #FEF3C7; color: #D97706; }
.dday-normal { background: #E0F2FE; color: #2563EB; }
.dday-safe { background: #F0FDF4; color: #16A34A; }

/* 섹션 헤더 */
.section-header {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
    margin: 8px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header .icon {
    font-size: 20px;
}

/* 필터 바 */
div[data-testid="stHorizontalBlock"] {
    gap: 8px;
}

/* Streamlit 기본 metric 숨기기 */
[data-testid="stMetricValue"] { font-size: 0; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# 데이터 로드
# ================================================================
config = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
paths = get_file_paths(config)
base = Path(__file__).resolve().parent.parent

medicines, devices = load_all(base / paths["medicine_csv"], base / paths["device_csv"])
log_path = base / get_log_path(config)
history = read_send_history(log_path) if log_path.exists() else []

today = date.today()

sent_set = {
    (r.category, r.target_year_month, r.alert_type)
    for r in history if r.status == "SUCCESS"
}


def _send_status(ym, cat="의약품"):
    s3 = (cat, ym, "3M") in sent_set
    s1 = (cat, ym, "1M") in sent_set
    if s3 and s1:
        return "발송완료(3M+1M)"
    elif s3:
        return "발송완료(3M)"
    elif s1:
        return "발송완료(1M)"
    return "미발송"


# ================================================================
# 헤더
# ================================================================
st.markdown("## 품목갱신 알림 대시보드")
st.caption(f"기준일: {today.strftime('%Y년 %m월 %d일')}")

# ================================================================
# 요약 카드 (3개)
# ================================================================
urgent_3m = (
    sum(1 for i in medicines if 0 <= (i.갱신신청기한 - today).days <= 90)
    + sum(1 for i in devices if 0 <= (i.갱신신청기한_시작 - today).days <= 90)
)
scheduled_6m = (
    sum(1 for i in medicines if 0 <= (i.갱신신청기한 - today).days <= 180)
    + sum(1 for i in devices if 0 <= (i.갱신신청기한_시작 - today).days <= 180)
)
total_items = len(medicines) + len(devices)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-card urgent">
        <div class="label">긴급 갱신 대상 (3개월 이내)</div>
        <div class="value">{urgent_3m}</div>
        <div class="sub">즉시 조치 필요</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card warning">
        <div class="label">예정된 갱신 (6개월 이내)</div>
        <div class="value">{scheduled_6m}</div>
        <div class="sub">사전 준비 권장</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card info">
        <div class="label">전체 관리 품목</div>
        <div class="value">{total_items}</div>
        <div class="sub">의약품 {len(medicines)} / 의료기기 {len(devices)}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ================================================================
# 필터 바
# ================================================================
fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 2])
with fc1:
    period = st.selectbox("조회 기간", ["3개월", "6개월", "9개월", "12개월", "전체"],
                          index=1, label_visibility="collapsed")
with fc2:
    cat_filter = st.selectbox("카테고리", ["전체", "의약품", "의료기기"],
                              label_visibility="collapsed")
with fc3:
    status_filter = st.selectbox("발송 상태", ["전체", "발송완료", "미발송"],
                                 label_visibility="collapsed")
with fc4:
    search = st.text_input("제품명/품목명 검색", label_visibility="collapsed",
                           placeholder="제품명 또는 품목명 검색...")

period_days = {"3개월": 90, "6개월": 180, "9개월": 270, "12개월": 365, "전체": 99999}
cutoff = today + timedelta(days=period_days[period])


# ================================================================
# D-day 스타일 함수
# ================================================================
def dday_text(d):
    if d < 0:
        return f"D+{abs(d)}"
    elif d == 0:
        return "D-Day"
    return f"D-{d}"


def highlight_dday(val):
    if isinstance(val, (int, float)):
        v = int(val)
        if v <= 0:
            return "background-color: #FEE2E2; color: #DC2626; font-weight: bold;"
        elif v < 30:
            return "background-color: #FEE2E2; color: #DC2626; font-weight: 600;"
        elif v < 90:
            return "background-color: #FEF3C7; color: #D97706;"
        elif v < 180:
            return "background-color: #E0F2FE; color: #2563EB;"
    return "color: #16A34A;"


def highlight_status(val):
    if isinstance(val, str):
        if val.startswith("발송완료"):
            return "background-color: #F0FDF4; color: #16A34A;"
        elif val == "미발송":
            return "background-color: #FEF3C7; color: #D97706;"
    return ""


# ================================================================
# 의약품 갱신 일정
# ================================================================
st.markdown('<div class="section-header"><span class="icon">💊</span> 의약품 갱신 일정</div>',
            unsafe_allow_html=True)

med_rows = []
for item in medicines:
    d_day = (item.갱신신청기한 - today).days
    ym = f"{item.갱신신청기한.year}-{item.갱신신청기한.month:02d}"
    med_rows.append({
        "제품명": item.제품명,
        "허가번호": item.허가번호,
        "품목유효기간": str(item.품목유효기간),
        "갱신신청기한": str(item.갱신신청기한),
        "D-day": d_day,
        "제조/수입": item.제조수입,
        "전문/일반": item.전문일반,
        "발송상태": _send_status(ym),
    })

df_med = pd.DataFrame(med_rows)

# 필터 적용
mask = pd.Series([True] * len(df_med))
if cat_filter == "의료기기":
    mask[:] = False
if period != "전체":
    mask &= (df_med["D-day"] >= 0) & (df_med["D-day"] <= period_days[period])
if status_filter == "발송완료":
    mask &= df_med["발송상태"].str.startswith("발송완료")
elif status_filter == "미발송":
    mask &= df_med["발송상태"] == "미발송"
if search:
    mask &= df_med["제품명"].str.contains(search, case=False, na=False)

df_med_f = df_med[mask].sort_values("D-day").reset_index(drop=True)

if cat_filter != "의료기기":
    cols = ["제품명", "허가번호", "품목유효기간", "갱신신청기한", "D-day", "제조/수입", "전문/일반", "발송상태"]
    styled = (df_med_f[cols].style
              .map(highlight_dday, subset=["D-day"])
              .map(highlight_status, subset=["발송상태"]))
    st.dataframe(styled, use_container_width=True, height=400, hide_index=True)
    st.caption(f"의약품 {len(df_med_f)}건")

# ================================================================
# 의료기기 갱신 일정
# ================================================================
st.markdown('<div class="section-header"><span class="icon">🔬</span> 의료기기 갱신 일정</div>',
            unsafe_allow_html=True)

dev_rows = []
for item in devices:
    d_day = (item.갱신신청기한_시작 - today).days
    ym = f"{item.갱신신청기한_시작.year}-{item.갱신신청기한_시작.month:02d}"
    dev_rows.append({
        "제품명": item.제품명,
        "품목명": item.품목명,
        "품목허가번호": item.품목허가번호,
        "유효기간": f"{item.유효기간_시작} ~ {item.유효기간_종료}",
        "갱신신청기한": f"{item.갱신신청기한_시작} ~ {item.갱신신청기한_종료}",
        "D-day": d_day,
        "제조/수입": item.제조수입,
        "발송상태": _send_status(ym, "의료기기"),
    })

df_dev = pd.DataFrame(dev_rows)

# 필터 적용
mask = pd.Series([True] * len(df_dev))
if cat_filter == "의약품":
    mask[:] = False
if period != "전체":
    mask &= (df_dev["D-day"] >= 0) & (df_dev["D-day"] <= period_days[period])
if status_filter == "발송완료":
    mask &= df_dev["발송상태"].str.startswith("발송완료")
elif status_filter == "미발송":
    mask &= df_dev["발송상태"] == "미발송"
if search:
    mask &= (df_dev["제품명"].str.contains(search, case=False, na=False)
             | df_dev["품목명"].str.contains(search, case=False, na=False))

df_dev_f = df_dev[mask].sort_values("D-day").reset_index(drop=True)

if cat_filter != "의약품":
    cols = ["제품명", "품목명", "품목허가번호", "유효기간", "갱신신청기한", "D-day", "제조/수입", "발송상태"]
    styled = (df_dev_f[cols].style
              .map(highlight_dday, subset=["D-day"])
              .map(highlight_status, subset=["발송상태"]))
    st.dataframe(styled, use_container_width=True, height=400, hide_index=True)
    st.caption(f"의료기기 {len(df_dev_f)}건")
