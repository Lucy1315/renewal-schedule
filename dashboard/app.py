import sys
from pathlib import Path

# src 모듈 import 경로 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st

st.set_page_config(
    page_title="품목갱신 알림 대시보드",
    page_icon="📋",
    layout="wide",
)

st.title("품목갱신 알림 자동화 대시보드")
st.markdown("좌측 메뉴에서 페이지를 선택하세요.")
st.markdown("""
- **개요**: KPI 카드 및 월별 추이 차트
- **갱신 대상 목록**: 필터 가능한 갱신 품목 테이블
- **발송 이력**: 알림 메일 발송 기록
- **데이터 품질**: 데이터 검증 결과
""")
