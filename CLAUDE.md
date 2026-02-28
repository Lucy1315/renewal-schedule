# CLAUDE.md

## Project

**품목갱신 알림 자동화(RPA) 및 대시보드** — 의약품/의료기기 품목허가 갱신 신청기한을 자동 알림(메일) 발송하고, 발송 이력 및 현황을 대시보드로 조회하는 시스템.

## Tech Stack

- **Language**: Python 3.11+
- **Excel 처리**: openpyxl (읽기/쓰기/스타일링)
- **메일 발송**: smtplib + email.mime (HTML 메일)
- **대시보드**: Streamlit
- **스케줄링**: cron / Windows Task Scheduler
- **로그/이력**: CSV
- **설정 관리**: YAML (config.yaml)

## Structure

```
re-approval/
├── CLAUDE.md
├── config.yaml                # 수신자, 파일경로, SMTP 설정 등
├── run_batch.py               # 배치 엔트리포인트 (cron용)
├── requirements.txt
├── data/
│   ├── 의약품갱신일정.csv
│   └── 의료기기갱신일정.csv
├── src/
│   ├── models.py              # dataclass (MedicineItem, DeviceItem, AlertTarget 등)
│   ├── config.py              # YAML 설정 로딩
│   ├── loader.py              # CSV 로딩 및 날짜 파싱 (edate, parse_date_range)
│   ├── rules.py               # 비즈니스 규칙 (알림 대상 산출)
│   ├── email_builder.py       # HTML 메일 본문/제목 생성
│   ├── mailer.py              # SMTP 발송 (retry 포함)
│   ├── excel_updater.py       # 발송 후 엑셀 붉은 테두리 표시
│   ├── send_log.py            # 발송 이력 CSV 읽기/쓰기, 멱등성 체크
│   └── main.py                # 배치 오케스트레이션
├── templates/
│   └── email_base.html        # HTML 이메일 템플릿
├── dashboard/
│   ├── app.py                 # Streamlit 메인
│   └── pages/
│       ├── 01_overview.py     # KPI 카드 + 월별 추이 차트
│       ├── 02_renewal_list.py # 갱신 목록 (필터, D-day, 알림상태)
│       ├── 03_send_history.py # 발송 이력 + drill-down
│       └── 04_data_quality.py # 데이터 검증 결과
├── logs/
│   └── send_history.csv       # 발송 이력 로그
└── tests/
    ├── test_loader.py
    ├── test_rules.py
    ├── test_email_builder.py
    └── test_send_log.py
```

## Commands

- `uv venv .venv && source .venv/bin/activate` — 가상환경 생성/활성화
- `uv pip install -r requirements.txt` — 의존성 설치
- `python run_batch.py` — 배치 실행
- `python run_batch.py --dry-run` — 실제 발송 없이 대상 확인 (HTML 미리보기 생성)
- `python run_batch.py --date 2026-05-19 --dry-run` — 특정 날짜로 테스트
- `streamlit run dashboard/app.py` — 대시보드 실행
- `python -m pytest tests/ -v` — 테스트 실행 (40개)

## Domain Rules (핵심 비즈니스 규칙)

### 의약품 알림
- **알림발송일** = 갱신신청기한 − 3개월 (EDATE 규칙)
- 배치 실행일(today) == 알림발송일이면 발송
- 메일 표: 동일 연도에서 대상 월 이상(>=) 품목 전체 포함
- 대상 월이 12월이면 **다음 연도 전체** 품목 추가

### 의료기기 알림
- **갱신신청기한**: 시작일 ~ 종료일 범위
- **알림발송일** = 시작일이 속한 달의 1일
- 배치 실행일(today) == 알림발송일이면 발송
- 메일 표: 동일 연도에서 대상 월 이상(>=) 품목 전체 포함
- 대상 월이 12월이면 **다음 연도 전체** 품목 추가

### 공통
- 메일 제목/본문에 "신청기한: YYYY년 MM월" 표기
- 메일 본문 표는 **HTML table**
- 발송 성공 시 엑셀 '갱신신청기한' 셀에 **붉은 테두리** 적용
- **멱등성**: 같은 대상 월 중복 발송 방지 (발송 이력 기반)
- 발송 실패 시 3회 재시도 → 최종 실패 시 운영자 알림

## Data Schema

### 의약품 시트 (의약품갱신일정.csv)
| 컬럼 | 타입 | 비고 |
|------|------|------|
| 제품명 | TEXT | |
| 허가일 | DATE | 예: 2017-02-20 |
| 품목유효기간 | DATE | 예: 2027-02-19 |
| **갱신신청기한** | **DATE** | **알림 기준**, 예: 2026-08-19 |
| 메일알람(3M전) | DATE | 파생값 (갱신신청기한 - 3개월), 예: 2026-05-19 |
| 업종 | TEXT | "의약품" |
| 제조/수입 | TEXT | "제조" 또는 "수입" |
| 허가번호 | TEXT | 예: 55 |
| 품목기준코드 | TEXT | 예: 201700895 |
| 전문/일반 | TEXT | "전문의약품" 또는 "일반의약품" |
| 품목분류 | TEXT | 예: "항악성종양제" |
| 허가/신고 | TEXT | "허가" 또는 "신고" |
| 유효기간 | TEXT | 예: "제조일로부터 36 개월" |
| 관계부처 | TEXT | 예: "대전청", "식약처" |

### 의료기기 시트 (의료기기갱신일정.csv)
| 컬럼 | 타입 | 비고 |
|------|------|------|
| 제품명 | TEXT | 복수 제품명 가능 (쉼표 구분, 줄바꿈 포함) |
| 품목명 | TEXT | 예: "폴리디옥사논봉합사" |
| 제조/수입 | TEXT | "제조" 또는 "수입" |
| 품목허가번호 | TEXT | 식별자, 예: "제허 25-352 호" |
| 허가일자 | DATE | 예: 2025-05-27 |
| 최종변경일 | DATE | |
| 유효기간 | TEXT (DATE RANGE) | "시작일 ~ 종료일" 형식, 예: "2025-05-27 ~ 2030-05-26" |
| **갱신신청기한** | **TEXT (DATE RANGE)** | **알림 기준**, "시작일 ~ 종료일" 파싱 필요, 예: "2029-08-30 ~ 2029-11-28" |
| 메일 알람 (3M전) | DATE | 파생값, 예: 2029-08-28 |

### 데이터 특이사항
- 의료기기 `제품명`에 줄바꿈·쌍따옴표 이스케이프 존재 → CSV 파싱 시 주의
- 의료기기 `유효기간`, `갱신신청기한`은 "YYYY-MM-DD ~ YYYY-MM-DD" 범위 문자열 → 분해 파싱 필요
- 의약품 `메일알람(3M전)` 컬럼이 이미 존재하지만, 규칙 엔진에서 직접 계산하여 검증하는 것을 권장
- 현재 의약품 26건, 의료기기 31건

## Conventions

- 언어: **한국어** (커밋 메시지, 주석, 문서)
- 코드: Python PEP 8, 타입 힌트 사용
- 날짜: `datetime.date` 사용, 타임존 KST
- 설정값(수신자, 경로, SMTP 등)은 코드에 하드코딩하지 않고 `config.yaml`로 분리
- 자격증명(SMTP 비밀번호 등)은 환경변수 또는 Secret 관리

## Validation Scenarios

1. 의약품: 갱신신청기한=2026-08-19 → 2026-05-19에 "신청 기한 2026년 8월" 메일 발송
2. 의약품(12월): 대상 월 12월이면 다음 연도 전체 포함
3. 의료기기: 시작일=2025-08-04 → 2025-08-01에 "신청 기한 2025년 8월" 메일 발송
4. 발송 성공 후 해당 품목 셀 붉은 테두리 적용 확인
5. 동일 대상 월 중복 발송 방지 확인

## Resolved Decisions

- [x] 메일 수신자: `jisoo.kim@samyang.com` (config.yaml)
- [x] 발신자: `popice76@gmail.com` (Gmail SMTP)
- [x] SMTP: Gmail (smtp.gmail.com:587, TLS), 앱 비밀번호는 환경변수 `SMTP_PASSWORD` (~/.zshrc에 설정)
- [x] 이메일 본문: "~까지인 품목 정보 안내" (templates/email_base.html)
- [x] Streamlit Cloud: https://renewal-schedule.streamlit.app (비공개 시 Sharing → Public 변경 필요)

## Pending Decisions

- [ ] 엑셀 저장 위치(SharePoint/네트워크) 및 파일명 규칙
- [ ] "붉은 박스" 정확한 스타일(색상코드, 테두리 두께) → config.yaml excel_update 섹션
