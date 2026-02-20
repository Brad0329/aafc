# AAFC 이관 데이터 정리 계획

> 목적: AWS 배포 전 오래된 데이터 정리 (2023년 이전 백업 후 삭제)
> 실행 환경: VS Code + Claude
> 실행 시점: 3월 말 최종 MSSQL 덤프 → PostgreSQL 이관 직후

---

## 정리 대상 테이블

| 테이블 (Django 모델) | DB 테이블명 | 기준 컬럼 | 예상 대상 |
|---|---|---|---|
| DailyTotalData | reports_dailytotaldata | course_ym | 500만 건 중 다수 |
| DailyCoachData | reports_dailycoachdata | course_ym | 일부 |
| DailyCoachDataNew | reports_dailycoachdatanew | course_ym | 574K 중 일부 |
| DailyCoachDataMonth | reports_dailycoachdatamonth | course_ym | 42K 중 일부 |

**기준: `course_ym < '2024-01'` (2023년 이전 전체)**

> ⚠️ course_ym 컬럼 타입이 `CharField`이므로 문자열 사전순 비교 적용.
> 모델별 저장 형식이 다름: DailyTotalData는 `'YYYY-MM'`, 나머지 3개는 `'YYYYMM'`.
> Management Command에서 각 모델별 cutoff 값을 분리 적용함 (STEP 2 참고).

---

## 작업 순서

### STEP 1. 삭제 전 백업 (필수)

```bash
# AWS RDS 최종 이관 직전, 전체 DB 백업
pg_dump -U aafc_user -h {RDS_ENDPOINT} -d aafc_prod -F c -f aafc_prod_before_cleanup.dump

# 또는 대상 테이블만 선택 백업
pg_dump -U aafc_user -h {RDS_ENDPOINT} -d aafc_prod \
  -t reports_dailytotaldata \
  -t reports_dailycoachdata \
  -t reports_dailycoachdatanew \
  -t reports_dailycoachdatamonth \
  -F c -f aafc_reports_backup_2023before.dump
```

> ⚠️ `aafc_user`, `aafc_prod`, `{RDS_ENDPOINT}`는 실제 배포 시 확정된 값으로 교체 필요.
> 배포 시 `.env` 파일 또는 별도 메모에 미리 정리해둘 것.

---

### STEP 2. course_ym 형식 확인

> ⚠️ 모델별 `course_ym` 저장 형식이 다릅니다. 이관 후 아래 SQL로 반드시 확인:
>
> | 테이블 | 형식 | cutoff |
> |---|---|---|
> | reports_dailytotaldata | `YYYY-MM` (하이픈 포함) | `'2024-01'` |
> | reports_dailycoachdata | `YYYYMM` (6자리) | `'202401'` |
> | reports_dailycoachdatanew | `YYYYMM` (6자리) | `'202401'` |
> | reports_dailycoachdatamonth | `YYYYMM` (6자리) | `'202401'` |

```sql
-- psql 접속 후 실행
SELECT DISTINCT course_ym FROM reports_dailytotaldata      WHERE course_ym < '2024-01' ORDER BY 1 LIMIT 20;
SELECT DISTINCT course_ym FROM reports_dailycoachdata      WHERE course_ym < '202401'  ORDER BY 1 LIMIT 20;
SELECT DISTINCT course_ym FROM reports_dailycoachdatanew   WHERE course_ym < '202401'  ORDER BY 1 LIMIT 20;
SELECT DISTINCT course_ym FROM reports_dailycoachdatamonth WHERE course_ym < '202401'  ORDER BY 1 LIMIT 20;
```

결과 형식이 위 표와 일치하면 다음 단계 진행.

---

### STEP 3. 삭제 대상 건수 확인 (dry-run)

```bash
python manage.py cleanup_old_data --dry-run --settings=config.settings.prod
```

출력 예시:
```
[DRY RUN] reports_dailytotaldata: 3,241,089건 삭제 예정 (course_ym < 2024-01)
[DRY RUN] reports_dailycoachdata: 45,231건 삭제 예정 (course_ym < 2024-01)
[DRY RUN] reports_dailycoachdatanew: 312,419건 삭제 예정 (course_ym < 2024-01)
[DRY RUN] reports_dailycoachdatamonth: 28,000건 삭제 예정 (course_ym < 2024-01)
```

---

### STEP 4. 실제 삭제 실행

```bash
python manage.py cleanup_old_data --settings=config.settings.prod
```

---

### STEP 5. 공간 회수 (필수)

```bash
# psql 접속 후 실행
psql -U aafc_user -h {RDS_ENDPOINT} -d aafc_prod

VACUUM ANALYZE reports_dailytotaldata;
VACUUM ANALYZE reports_dailycoachdata;
VACUUM ANALYZE reports_dailycoachdatanew;
VACUUM ANALYZE reports_dailycoachdatamonth;
```

---

### STEP 6. 롤백 절차 (문제 발생 시)

```bash
# 전체 DB 복구 (기존 DB 삭제 후 복원)
dropdb -U aafc_user -h {RDS_ENDPOINT} aafc_prod
createdb -U aafc_user -h {RDS_ENDPOINT} aafc_prod
pg_restore -U aafc_user -h {RDS_ENDPOINT} -d aafc_prod aafc_prod_before_cleanup.dump

# 또는 대상 테이블만 복원 (기존 테이블 데이터 남아있는 경우)
pg_restore -U aafc_user -h {RDS_ENDPOINT} -d aafc_prod \
  -t reports_dailytotaldata \
  -t reports_dailycoachdata \
  -t reports_dailycoachdatanew \
  -t reports_dailycoachdatamonth \
  aafc_reports_backup_2023before.dump
```

---

## Management Command

`apps/reports/management/commands/cleanup_old_data.py` 파일이 이미 작성되어 있음.

주요 동작:
- `--dry-run` 옵션: 실제 삭제 없이 대상 건수만 출력
- 배치 삭제: 한 번에 10,000건씩 반복 (DB 락 방지)
- 진행 상황 출력 (10,000건 단위)
- 완료 후 총 삭제 건수 요약

---

## 로컬에서 리허설 방법

3월 말 실제 이관 전, 로컬 개발 DB(2월 9일 스냅샷)에서 미리 테스트:

```bash
# 1. course_ym 형식 확인 (psql)
psql -U postgres -d aafc_dev
SELECT DISTINCT course_ym FROM reports_dailytotaldata WHERE course_ym < '2024-01' ORDER BY 1 LIMIT 20;

# 2. dry-run으로 대상 확인
python manage.py cleanup_old_data --dry-run

# 3. 실제 삭제 테스트
python manage.py cleanup_old_data

# 4. 리포트 페이지 정상 동작 확인 (2024년 이후 데이터 조회)
python manage.py runserver
```

---

## 3월 말 최종 이관 체크리스트

- [ ] MSSQL 최신 덤프 (3월 말 기준)
- [ ] 로컬에서 PostgreSQL 이관 스크립트 실행
- [ ] RDS 접속 정보 확정 (`{RDS_ENDPOINT}`, `aafc_user`, `aafc_prod` 실제 값 확인)
- [ ] `course_ym` 형식 이상 여부 SQL 확인
- [ ] `cleanup_old_data --dry-run` 으로 삭제 대상 건수 확인
- [ ] 사용자에게 최종 확인 (2023년 이전 데이터 삭제 동의)
- [ ] 전체 DB 백업 (`aafc_prod_before_cleanup.dump`)
- [ ] 대상 테이블 선택 백업 (`aafc_reports_backup_2023before.dump`)
- [ ] `cleanup_old_data` 실행
- [ ] `VACUUM ANALYZE` 실행 (4개 테이블)
- [ ] 리포트 페이지 정상 동작 확인
- [ ] AWS RDS에 최종 데이터 업로드
