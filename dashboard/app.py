import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import streamlit as st

from config import load_config, get_file_paths, get_log_path
from email_builder import build_email_body, build_email_subject
from loader import load_all
from models import AlertTarget, Category
from rules import _collect_device_table_items, _collect_medicine_table_items
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
/* 카드 */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 24px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-top: 4px solid #ddd;
    text-align: center;
    min-height: 120px;
}
.metric-card.urgent { border-top-color: #EF4444; }
.metric-card.warning { border-top-color: #F59E0B; }
.metric-card.info { border-top-color: #3B82F6; }
.metric-card .label {
    font-size: 13px; color: #6B7280; margin-bottom: 6px; font-weight: 500;
}
.metric-card .value {
    font-size: 40px; font-weight: 700; color: #111827; line-height: 1.1;
}
.metric-card .sub {
    font-size: 12px; color: #9CA3AF; margin-top: 6px;
}

/* 섹션 헤더 */
.section-title {
    font-size: 17px; font-weight: 700; color: #1F2937;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #E5E7EB;
}
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

# ================================================================
# 헤더
# ================================================================
st.markdown("## 품목갱신 알림 대시보드")
st.caption(f"기준일: {today.strftime('%Y년 %m월 %d일')}  |  의약품 {len(medicines)}건  ·  의료기기 {len(devices)}건")

# ================================================================
# 요약 카드 (3개)
# ================================================================
urgent_3m = (
    sum(1 for i in medicines
        if any(today <= d <= today + timedelta(days=90) for d in [i.알림발송일, i.알림발송일_1M]))
    + sum(1 for i in devices
          if any(today <= d <= today + timedelta(days=90) for d in [i.알림발송일, i.알림발송일_1M]))
)
scheduled_6m = (
    sum(1 for i in medicines
        if any(today <= d <= today + timedelta(days=180) for d in [i.알림발송일, i.알림발송일_1M]))
    + sum(1 for i in devices
          if any(today <= d <= today + timedelta(days=180) for d in [i.알림발송일, i.알림발송일_1M]))
)
total_items = len(medicines) + len(devices)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-card urgent">
        <div class="label">긴급 갱신 대상</div>
        <div class="value">{urgent_3m}</div>
        <div class="sub">3개월 이내 알림 예정</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card warning">
        <div class="label">예정된 갱신</div>
        <div class="value">{scheduled_6m}</div>
        <div class="sub">6개월 이내 알림 예정</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card info">
        <div class="label">전체 품목</div>
        <div class="value">{total_items}</div>
        <div class="sub">의약품 {len(medicines)} / 의료기기 {len(devices)}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ================================================================
# 필터 바
# ================================================================
fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 2])
with fc1:
    st.caption("알림 기간")
    period = st.selectbox("알림 기간", ["전체", "3개월", "6개월", "9개월", "12개월", "직접 설정"],
                          label_visibility="collapsed")
with fc2:
    st.caption("분류")
    cat_filter = st.selectbox("분류", ["전체", "전문의약품", "일반의약품", "의료기기"],
                              label_visibility="collapsed")
with fc3:
    st.caption("제조/수입")
    mfg_filter = st.selectbox("제조/수입", ["전체", "제조", "수입"],
                              label_visibility="collapsed")
with fc4:
    st.caption("검색")
    search = st.text_input("검색", label_visibility="collapsed",
                           placeholder="제품명 또는 품목명 검색...")

if period == "직접 설정":
    dc1, dc2 = st.columns(2)
    with dc1:
        date_from = st.date_input("시작일", value=today)
    with dc2:
        date_to = st.date_input("종료일", value=today + timedelta(days=180))
else:
    date_from = today
    period_days = {"전체": 99999, "3개월": 90, "6개월": 180, "9개월": 270, "12개월": 365}
    date_to = today + timedelta(days=period_days[period])


# ================================================================
# D-day / 상태 스타일
# ================================================================
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


# ================================================================
# 의약품 갱신 일정
# ================================================================
st.markdown('<div class="section-title">의약품 갱신 일정</div>', unsafe_allow_html=True)

med_rows = []
for item in medicines:
    d_day = (item.갱신신청기한 - today).days
    alert_dates = [d for d in [item.알림발송일, item.알림발송일_1M] if d >= today]
    nearest_alert = min(alert_dates) if alert_dates else item.알림발송일
    med_rows.append({
        "제품명": item.제품명,
        "품목유효기간": str(item.품목유효기간),
        "갱신신청기한": str(item.갱신신청기한),
        "제조/수입": item.제조수입,
        "허가번호": item.허가번호,
        "관계부처": item.관계부처,
        "D-Day": d_day,
        "_알림일": nearest_alert,
        "_전문일반": item.전문일반,
    })

df_med = pd.DataFrame(med_rows)

# 필터
mask_med = pd.Series([True] * len(df_med))
if cat_filter == "의료기기":
    mask_med[:] = False
elif cat_filter == "전문의약품":
    mask_med &= df_med["_전문일반"] == "전문의약품"
elif cat_filter == "일반의약품":
    mask_med &= df_med["_전문일반"] == "일반의약품"
if period != "전체":
    mask_med &= df_med["_알림일"].apply(lambda d: date_from <= d <= date_to)
if mfg_filter != "전체":
    mask_med &= df_med["제조/수입"] == mfg_filter
if search:
    mask_med &= df_med["제품명"].str.contains(search, case=False, na=False)

df_med_f = df_med[mask_med].sort_values("D-Day").reset_index(drop=True)

if cat_filter != "의료기기":
    display_cols = ["제품명", "품목유효기간", "갱신신청기한", "제조/수입", "허가번호", "관계부처", "D-Day"]
    styled = df_med_f[display_cols].style.map(highlight_dday, subset=["D-Day"])
    st.dataframe(styled, use_container_width=True, height=400, hide_index=True)
    st.caption(f"의약품 {len(df_med_f)}건")

# ================================================================
# 의료기기 갱신 일정
# ================================================================
st.markdown('<div class="section-title">의료기기 갱신 일정</div>', unsafe_allow_html=True)

dev_rows = []
for item in devices:
    d_day = (item.갱신신청기한_시작 - today).days
    alert_dates = [d for d in [item.알림발송일, item.알림발송일_1M] if d >= today]
    nearest_alert = min(alert_dates) if alert_dates else item.알림발송일
    dev_rows.append({
        "제품명": item.제품명,
        "품목명": item.품목명,
        "제조/수입": item.제조수입,
        "품목허가번호": item.품목허가번호,
        "품목유효기간": f"{item.유효기간_시작} ~ {item.유효기간_종료}",
        "갱신신청기한": f"{item.갱신신청기한_시작} ~ {item.갱신신청기한_종료}",
        "D-Day": d_day,
        "_알림일": nearest_alert,
    })

df_dev = pd.DataFrame(dev_rows)

# 필터
mask_dev = pd.Series([True] * len(df_dev))
if cat_filter in ("전문의약품", "일반의약품"):
    mask_dev[:] = False
if period != "전체":
    mask_dev &= df_dev["_알림일"].apply(lambda d: date_from <= d <= date_to)
if mfg_filter != "전체":
    mask_dev &= df_dev["제조/수입"] == mfg_filter
if search:
    mask_dev &= (df_dev["제품명"].str.contains(search, case=False, na=False)
                 | df_dev["품목명"].str.contains(search, case=False, na=False))

df_dev_f = df_dev[mask_dev].sort_values("D-Day").reset_index(drop=True)

if cat_filter not in ("전문의약품", "일반의약품"):
    display_cols = ["제품명", "품목명", "제조/수입", "품목허가번호", "품목유효기간", "갱신신청기한", "D-Day"]
    styled = df_dev_f[display_cols].style.map(highlight_dday, subset=["D-Day"])
    st.dataframe(styled, use_container_width=True, height=400, hide_index=True)
    st.caption(f"의료기기 {len(df_dev_f)}건")

# ================================================================
# 이메일 미리보기
# ================================================================
st.markdown('<div class="section-title">이메일 미리보기</div>', unsafe_allow_html=True)

ec1, ec2, ec3 = st.columns([1, 1, 1])
with ec1:
    email_cat = st.selectbox("카테고리", ["의약품", "의료기기"], key="email_cat")
with ec2:
    if email_cat == "의약품":
        target_months = sorted(set(
            f"{i.갱신신청기한.year}-{i.갱신신청기한.month:02d}" for i in medicines
        ))
    else:
        target_months = sorted(set(
            f"{i.갱신신청기한_시작.year}-{i.갱신신청기한_시작.month:02d}" for i in devices
        ))
    selected_ym = st.selectbox("대상월", target_months, key="email_ym")
with ec3:
    email_type = st.selectbox("알림 유형", ["3M", "1M"], key="email_type")

if selected_ym:
    year, month = map(int, selected_ym.split("-"))
    if email_cat == "의약품":
        items_hl = _collect_medicine_table_items(medicines, year, month)
        alert = AlertTarget(Category.MEDICINE, year, month, email_type, items_hl)
        subject = build_email_subject(Category.MEDICINE, year, month, email_type)
    else:
        items_hl = _collect_device_table_items(devices, year, month)
        alert = AlertTarget(Category.DEVICE, year, month, email_type, items_hl)
        subject = build_email_subject(Category.DEVICE, year, month, email_type)

    html_body = build_email_body(alert)

    st.text_input("제목", value=subject, disabled=True)

    with st.expander("미리보기 열기", expanded=False):
        st.components.v1.html(html_body, height=500, scrolling=True)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "HTML 다운로드",
            data=html_body,
            file_name=f"email_{email_cat}_{selected_ym}_{email_type}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_dl2:
        st.code(subject, language=None)
