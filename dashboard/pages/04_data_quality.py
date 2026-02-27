import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import csv
import pandas as pd
import streamlit as st

from config import load_config, get_file_paths
from loader import load_device_csv, load_medicine_csv, parse_date, parse_date_range

st.header("데이터 품질 검증")

config = load_config(Path(__file__).resolve().parent.parent.parent / "config.yaml")
paths = get_file_paths(config)
base = Path(__file__).resolve().parent.parent.parent

issues = []

# --- 의약품 검증 ---
st.subheader("의약품")
med_path = base / paths["medicine_csv"]
med_required = ["제품명", "허가일", "품목유효기간", "갱신신청기한"]

try:
    with open(med_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # 필수 컬럼 검사
        missing = [c for c in med_required if c not in headers]
        if missing:
            st.error(f"필수 컬럼 누락: {missing}")
            issues.append({"파일": "의약품", "문제": "필수 컬럼 누락", "상세": str(missing)})
        else:
            st.success("필수 컬럼 모두 존재")

        # 날짜 파싱 검사
        parse_errors = []
        row_count = 0
        for idx, row in enumerate(reader, start=1):
            row_count += 1
            for col in ["허가일", "품목유효기간", "갱신신청기한"]:
                try:
                    parse_date(row[col])
                except Exception as e:
                    parse_errors.append({"행": idx, "컬럼": col, "값": row[col], "에러": str(e)})

        if parse_errors:
            st.warning(f"날짜 파싱 실패: {len(parse_errors)}건")
            st.dataframe(pd.DataFrame(parse_errors), width="stretch")
            issues.extend([{"파일": "의약품", **e} for e in parse_errors])
        else:
            st.success(f"날짜 파싱: {row_count}건 모두 성공")

except FileNotFoundError:
    st.error(f"파일 없음: {med_path}")

st.divider()

# --- 의료기기 검증 ---
st.subheader("의료기기")
dev_path = base / paths["device_csv"]
dev_required = ["품목명", "품목허가번호", "허가일자", "유효기간", "갱신신청기한"]

try:
    with open(dev_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        missing = [c for c in dev_required if c not in headers]
        if missing:
            st.error(f"필수 컬럼 누락: {missing}")
        else:
            st.success("필수 컬럼 모두 존재")

        # 날짜 파싱 + 범위 파싱 검사
        parse_errors = []
        dup_check = {}
        multiline_names = []
        row_count = 0

        for idx, row in enumerate(reader, start=1):
            row_count += 1
            # 날짜 범위 파싱
            for col in ["유효기간", "갱신신청기한"]:
                try:
                    parse_date_range(row[col])
                except Exception as e:
                    parse_errors.append({"행": idx, "컬럼": col, "값": row[col], "에러": str(e)})

            # 단일 날짜 파싱
            for col in ["허가일자", "최종변경일"]:
                try:
                    parse_date(row[col])
                except Exception as e:
                    parse_errors.append({"행": idx, "컬럼": col, "값": row[col], "에러": str(e)})

            # 중복 키 검사 (품목허가번호)
            key = row["품목허가번호"].strip()
            if key in dup_check:
                issues.append({
                    "파일": "의료기기",
                    "문제": "중복 품목허가번호",
                    "상세": f"행 {dup_check[key]}와 행 {idx}: {key}",
                })
            dup_check[key] = idx

            # 줄바꿈 제품명
            if "\n" in row["제품명"]:
                multiline_names.append({"행": idx, "제품명": repr(row["제품명"][:50])})

        if parse_errors:
            st.warning(f"날짜 파싱 실패: {len(parse_errors)}건")
            st.dataframe(pd.DataFrame(parse_errors), width="stretch")
        else:
            st.success(f"날짜 파싱: {row_count}건 모두 성공")

        # 중복 키
        dup_issues = [i for i in issues if i.get("문제") == "중복 품목허가번호"]
        if dup_issues:
            st.warning(f"중복 품목허가번호: {len(dup_issues)}건")
            st.dataframe(pd.DataFrame(dup_issues), width="stretch")
        else:
            st.success("중복 키 없음")

        # 줄바꿈 제품명
        if multiline_names:
            st.info(f"줄바꿈 포함 제품명: {len(multiline_names)}건 (로딩 시 자동 처리됨)")
            with st.expander("상세 보기"):
                st.dataframe(pd.DataFrame(multiline_names), width="stretch")
        else:
            st.success("줄바꿈 포함 제품명 없음")

except FileNotFoundError:
    st.error(f"파일 없음: {dev_path}")

# --- 전체 요약 ---
st.divider()
st.subheader("전체 요약")
if issues:
    st.warning(f"총 {len(issues)}건의 이슈 발견")
    st.dataframe(pd.DataFrame(issues), width="stretch")
else:
    st.success("데이터 품질 이슈 없음")
