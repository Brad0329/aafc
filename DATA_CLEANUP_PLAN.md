# AAFC 이관 데이터 정리 계획

> 목적: AWS 배포 전 불필요한 집계 테이블 제거
> 실행 환경: VS Code + Claude
> 실행 시점: 3월 말 최종 MSSQL 덤프 → PostgreSQL 이관 직후

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-02-18 | 최초 작성 (4개 집계 테이블 데이터 정리 계획) |
| 2026-02-20 | DailyTotalData 모델 제거 (commit 6987103) |
| 2026-02-22 | DailyCoachData/New/Month → 뷰 미사용 전환 (commit 5fe7879) |

---

## 현황: 집계 테이블 정리 완료

4개 REPORT 뷰(`report_pay_master`, `report_month_coachdata`, `report_each_coachdata`, `report_year_coachdata`)가
Enrollment 원본 테이블에서 직접 조회하도록 변경됨 (commit 5fe7879).

| 테이블 (Django 모델) | DB 테이블명 | 건수 | 상태 |
|---|---|---|---|
| ~~DailyTotalData~~ | ~~reports_dailytotaldata~~ | ~~5,094,089~~ | **모델 제거됨 (commit 6987103)** |
| ~~DailyCoachData~~ | ~~reports_dailycoachdata~~ | ~~66,787~~ | **뷰 미사용 → 모델 제거 예정** |
| ~~DailyCoachDataNew~~ | ~~reports_dailycoachdatanew~~ | ~~574,419~~ | **뷰 미사용 → 모델 제거 예정** |
| ~~DailyCoachDataMonth~~ | ~~reports_dailycoachdatamonth~~ | ~~42,785~~ | **뷰 미사용 → 모델 제거 예정** |

> 이 테이블들은 MSSQL SQL Server Agent 배치 잡(매일 23시)이 생성하던 사전집계 테이블.
> Django에는 이 배치 프로세스가 없어서 새 데이터가 생성되지 않음.
> → **데이터 정리 대신 모델 자체를 제거하는 것이 올바른 접근.**

---

## 모델 제거 작업 순서

### STEP 1. 코드에서 모델 제거

```bash
# 1. reports/models.py에서 3개 모델 클래스 삭제
#    - DailyCoachData
#    - DailyCoachDataNew
#    - DailyCoachDataMonth
#    (MonthlyData는 유지)

# 2. reports/admin.py에서 3개 Admin 클래스 삭제

# 3. views_report.py에서 import 확인 (이미 제거됨 - commit 5fe7879)

# 4. 마이그레이션 생성 및 적용
python manage.py makemigrations reports
python manage.py migrate
```

### STEP 2. 관련 파일 정리

```bash
# cleanup_old_data management command 삭제 (더 이상 불필요)
# 경로: apps/reports/management/commands/cleanup_old_data.py

# migrate_reports.py에서 관련 이관 함수 제거
# 경로: scripts/migrate_reports.py
```

### STEP 3. 이관 시 해당 테이블 스킵

3월 말 최종 MSSQL 이관 시 아래 MSSQL 테이블은 **이관하지 않음**:
- `lf_daily_coachdata` (→ DailyCoachData)
- `lf_daily_coachdata_new` (→ DailyCoachDataNew)
- `lf_daily_coachdata_new_month` (→ DailyCoachDataMonth)
- `lf_daily_total_data` (→ DailyTotalData, 이미 제거됨)

---

## 3월 말 최종 이관 체크리스트

- [ ] MSSQL 최신 덤프 (3월 말 기준)
- [ ] 로컬에서 PostgreSQL 이관 스크립트 실행 (위 4개 테이블 제외)
- [ ] RDS 접속 정보 확정 (`{RDS_ENDPOINT}`, `aafc_user`, `aafc_prod` 실제 값 확인)
- [ ] `python manage.py migrate` → 집계 테이블 DROP 확인
- [ ] 리포트 페이지 정상 동작 확인 (Enrollment 직접 조회 방식)
- [ ] AWS RDS에 최종 데이터 업로드
