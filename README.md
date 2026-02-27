# 품목갱신 알림 자동화(RPA) 및 대시보드

의약품/의료기기 품목허가 갱신 신청기한을 자동으로 알림(메일) 발송하고, 발송 이력 및 현황을 대시보드로 조회하는 시스템입니다.

## 주요 기능

- **자동 이메일 알림**: 갱신 신청기한 3개월 전 / 1개월 전 자동 발송
- **멱등성 보장**: 동일 대상월 중복 발송 방지 (발송 이력 기반)
- **실패 재시도**: 발송 실패 시 최대 3회 자동 재시도 (1/3/9초 백오프)
- **Streamlit 대시보드**: 갱신 현황, 목록, 발송 이력, 데이터 품질 검증

## 대시보드

> **Live**: [https://renewal-schedule.streamlit.app](https://renewal-schedule.streamlit.app)

| 페이지 | 설명 |
|--------|------|
| **개요** | KPI 카드 (이번달/다음달 알림), 월별 추이, 카테고리 분포, 발송 상태 요약 |
| **갱신 대상 목록** | 전체/의약품/의료기기 탭, D-day 색상 표시, 필터(연도/상태/검색) |
| **발송 이력** | 발송 로그 + 필터 + Drill-down(대상월별 품목 상세) |
| **데이터 품질** | 필수 컬럼, 날짜 파싱, 중복 키, 줄바꿈 검증 |

## 기술 스택

- **Python** 3.11+
- **Streamlit** — 대시보드
- **smtplib + email.mime** — HTML 이메일 발송
- **openpyxl** — 엑셀 읽기/쓰기
- **PyYAML** — 설정 관리

## 프로젝트 구조

```
re-approval/
├── config.yaml                # 수신자, 파일경로, SMTP 설정
├── run_batch.py               # 배치 엔트리포인트 (cron용)
├── requirements.txt
├── data/
│   ├── 의약품갱신일정.csv
│   └── 의료기기갱신일정.csv
├── src/
│   ├── models.py              # 데이터 모델 (MedicineItem, DeviceItem 등)
│   ├── config.py              # YAML 설정 로딩
│   ├── loader.py              # CSV 로딩 및 날짜 파싱
│   ├── rules.py               # 알림 대상 산출 규칙
│   ├── email_builder.py       # HTML 메일 본문/제목 생성
│   ├── mailer.py              # SMTP 발송 (retry 포함)
│   ├── excel_updater.py       # 발송 후 엑셀 표시
│   ├── send_log.py            # 발송 이력 관리, 멱등성 체크
│   └── main.py                # 배치 오케스트레이션
├── templates/
│   └── email_base.html        # HTML 이메일 템플릿
├── dashboard/
│   ├── app.py                 # Streamlit 메인
│   └── pages/
│       ├── 01_overview.py     # 개요
│       ├── 02_renewal_list.py # 갱신 대상 목록
│       ├── 03_send_history.py # 발송 이력
│       └── 04_data_quality.py # 데이터 품질 검증
├── logs/
│   └── send_history.csv       # 발송 이력 로그
└── tests/                     # 테스트 (45개)
```

## 설치 및 실행

```bash
# 가상환경 생성 및 활성화
uv venv .venv && source .venv/bin/activate

# 의존성 설치
uv pip install -r requirements.txt
```

### 배치 실행 (이메일 발송)

```bash
# 오늘 날짜 기준 실행
python run_batch.py

# 미리보기 (실제 발송 없음)
python run_batch.py --dry-run

# 특정 날짜로 테스트
python run_batch.py --date 2026-05-19 --dry-run
```

### 대시보드 실행

```bash
streamlit run dashboard/app.py
```

### 테스트

```bash
python -m pytest tests/ -v
```

## 알림 규칙

### 의약품

| 항목 | 규칙 |
|------|------|
| **3M 알림발송일** | 갱신신청기한 − 3개월 (EDATE) |
| **1M 알림발송일** | 갱신신청기한 − 1개월 (EDATE) |
| **발송 조건** | 배치 실행일 == 알림발송일 |
| **메일 테이블** | 동일 연도, 대상 월 이상(>=) 품목 전체 포함 |

### 의료기기

| 항목 | 규칙 |
|------|------|
| **3M 알림발송일** | 갱신신청기한 시작일 − 3개월 (EDATE) |
| **1M 알림발송일** | 갱신신청기한 시작일 − 1개월 (EDATE) |
| **발송 조건** | 배치 실행일 == 알림발송일 |
| **메일 테이블** | 동일 연도, 대상 월 이상(>=) 품목 전체 포함 |

### 공통

- 대상 월이 **12월**이면 다음 연도 전체 품목 추가
- 대상 월 품목만 **노란 하이라이트** 표시
- 멱등성: `(카테고리, 대상월, 알림유형)` 기준 중복 발송 방지

## 환경 변수

| 변수 | 설명 |
|------|------|
| `SMTP_PASSWORD` | Gmail 앱 비밀번호 |

## 데이터

- 의약품: 26건 (`data/의약품갱신일정.csv`)
- 의료기기: 31건 (`data/의료기기갱신일정.csv`)

## 라이선스

Private
