# Phase 7: 리포트 + 통계 구현 계획

## Context
Phase 6까지 완료된 AAFC 시스템에 리포트/통계 기능을 추가한다. 기존 ASP의 ba_office/report/ 하위 49개 파일에 해당하는 데이터 계층을 구축하고, Django Admin 기반 관리 + 기본 보고서 뷰 + Excel 다운로드를 구현한다. Phase 8(ba_office UI 복제)의 데이터 기반이 된다.

## MSSQL 원본 테이블 (8개)

| 테이블 | 건수 | 대상 앱 |
|--------|------|---------|
| lf_student_attendance | 231,147 | enrollment |
| lf_change_history | 877 | enrollment |
| lf_wait_student | 107 | enrollment (이관 완료) |
| lf_daily_total_data | 5,094,089 | reports |
| lf_daily_coachdata | 66,787 | reports |
| lf_daily_coachdata_new | 574,419 | reports |
| lf_daily_coachdata_new_month | 42,785 | reports |
| lf_monthly_data | 28,588 | reports |

---

## 작업 순서

### Step 1: 모델 생성

#### 1-1. enrollment 앱에 추가 (apps/enrollment/models.py)

**Attendance** ← lf_student_attendance (231,147건)
```
- local_code: IntegerField (권역코드)
- sta_code: IntegerField (구장코드)
- lecture_code: IntegerField (강좌코드)
- child_id: CharField(30) (자녀ID)
- attendance_dt: CharField(10) (출석일 YYYY-MM-DD)
- attendance_gbn: CharField(1) (Y=출석/N=결석/A=보강/R=우천취소/D=수업연기/E=출결제외)
- attendance_desc: CharField(100) (비고)
- insert_dt: DateTimeField
- insert_id: CharField(16)
- mata: CharField(1)
- app_month: CharField(7) (적용월 YYYYMM)
- complete_yn: CharField(1)
- uid: IntegerField
- match_ymd: CharField(8) (매칭일)
- ticket_no: CharField(20)
- ticket_no2: CharField(20)
인덱스: (attendance_dt), (child_id), (lecture_code, attendance_dt), (sta_code)
```

**ChangeHistory** ← lf_change_history (877건)
```
- member_id: CharField(30)
- child_id: CharField(30)
- chg_gbn: CharField(10) (변경구분: 강좌변경 등)
- chg_desc: CharField(100) (변경설명)
- no_seq: IntegerField (입단번호)
- src_seq: IntegerField (원본번호)
- reg_dt: DateTimeField
- reg_id: CharField(30)
```

#### 1-2. reports 앱 모델 생성 (apps/reports/models.py)

**DailyTotalData** ← lf_daily_total_data (5,094,089건)
```
- proc_dt: CharField(12) (처리일)
- member_id: CharField(30)
- member_name: CharField(30)
- child_id: CharField(30)
- mhtel: CharField(30)
- child_name: CharField(30)
- card_num: CharField(8)
- apply_gubun: CharField(30)
- sta_name: CharField(50)
- lecture_code: IntegerField
- lecture_title: CharField(150)
- coach_name: CharField(30)
- lec_cycle: CharField(1)
- lec_period: CharField(1)
- lecture_stats: CharField(30)
- pay_price: IntegerField
- lec_price: IntegerField
- join_price: IntegerField
- lec_course_ym_amt: IntegerField
- pay_stats: CharField(12)
- pay_method: CharField(14)
- pay_dt: CharField(10)
- cancel_date: CharField(10)
- cancel_code: CharField(4)
- cancel_desc: CharField(100)
- start_dt: CharField(6)
- end_dt: CharField(6)
- course_ym: CharField(7)
- course_ym_amt: IntegerField
- insert_id: CharField(16)
- insert_dt: CharField(10)
인덱스: (proc_dt), (member_id), (sta_name), (course_ym), (pay_stats)
```

**DailyCoachData** ← lf_daily_coachdata (66,787건)
```
- course_ym: CharField(10)
- lgbn_name: CharField(30) (리그구분)
- sta_name: CharField(40)
- coach_name: CharField(40)
- member_id: CharField(30)
- child_id: CharField(30)
- cl_cnt: IntegerField (수업횟수)
- m1001_price ~ m2002_price: IntegerField × 8 (청구코드별 금액)
- regdate: DateTimeField
- master_seq: IntegerField
인덱스: (course_ym)
```

**DailyCoachDataNew** ← lf_daily_coachdata_new (574,419건)
```
- proc_dt: CharField(8)
- pay_seq: IntegerField
- member_id: CharField(30)
- child_id: CharField(30)
- order_id: CharField(50)
- pay_dt: DateTimeField
- insert_dt: DateTimeField
- pay_method: CharField(20)
- course_ym: CharField(10)
- sta_code: IntegerField
- lecture_code: IntegerField
- coach_code: IntegerField
- coach_name: CharField(30)
- cl_cnt: IntegerField
- m1001_price ~ m2002_price: IntegerField × 8
- regdate: DateTimeField
인덱스: (course_ym), (proc_dt)
```

**DailyCoachDataMonth** ← lf_daily_coachdata_new_month (42,785건)
```
- DailyCoachDataNew와 동일 + new_coach_code, new_coach_name 추가
인덱스: (course_ym)
```

**MonthlyData** ← lf_monthly_data (28,588건)
```
- proc_dt: CharField(20)
- code_desc: CharField(50) (코드설명)
- sta_name: CharField(50)
- sta_code: IntegerField
- m_cnt: IntegerField (회원수)
- goal_cnt: IntegerField (목표수)
- tocl: IntegerField (총수업)
- newT_appl_cnt ~ stats_lnF_cnt: IntegerField × 8 (통계 항목)
- regdate: DateTimeField
인덱스: (proc_dt), (sta_code)
```

### Step 2: makemigrations + migrate

### Step 3: Django Admin 등록

**apps/enrollment/admin.py** - Attendance, ChangeHistory Admin 추가
- Attendance: list_display(출석일/구장/강좌/자녀/출결), list_filter(attendance_gbn/complete_yn), search_fields, date_hierarchy=None (CharField이므로)
- ChangeHistory: list_display(변경구분/설명/회원/자녀/일시), list_filter(chg_gbn)

**apps/reports/admin.py** - 5개 모델 Admin 등록
- 각 모델: list_display, list_filter, search_fields, ordering
- DailyTotalData: readonly (보고서 데이터이므로)

### Step 4: 데이터 이관 스크립트 (scripts/migrate_reports.py)

기존 패턴 따름 (safe_str, checkint, make_aware 헬퍼):
1. migrate_attendance() - lf_student_attendance → Attendance (231K건, 배치 1만건)
2. migrate_change_history() - lf_change_history → ChangeHistory (877건)
3. migrate_daily_total_data() - lf_daily_total_data → DailyTotalData (5M건, 배치 1만건, cursor.fetchmany 사용)
4. migrate_daily_coachdata() - lf_daily_coachdata → DailyCoachData (67K건)
5. migrate_daily_coachdata_new() - lf_daily_coachdata_new → DailyCoachDataNew (574K건, 배치 1만건)
6. migrate_daily_coachdata_month() - lf_daily_coachdata_new_month → DailyCoachDataMonth (43K건)
7. migrate_monthly_data() - lf_monthly_data → MonthlyData (29K건)

**대용량 테이블 처리**: bulk_create(batch_size=5000) + cursor.fetchmany(10000) 조합으로 메모리 효율적 처리

### Step 5: 보고서 뷰 + 템플릿 + Excel 다운로드

Phase 8에서 ba_office UI를 구축하므로, Phase 7에서는 Django Admin 확장으로 기본 보고서 기능 제공:

**apps/reports/views.py** - 관리자 전용 보고서 뷰:
1. `total_data_view` - 전체 DATA 목록 (필터: 기간/구장/결제상태/결제방법)
2. `total_data_excel` - 전체 DATA Excel 다운로드
3. `coach_stats_view` - 코치별 통계 (필터: 년월/구장/코치)
4. `coach_stats_excel` - 코치별 통계 Excel 다운로드
5. `attendance_report_view` - 출석 통계 (필터: 년월/구장/강좌)
6. `attendance_report_excel` - 출석 Excel 다운로드
7. `monthly_stats_view` - 월별 구장 통계
8. `monthly_stats_excel` - 월별 통계 Excel

**apps/reports/urls.py** - URL 패턴 (prefix: /reports/)

**config/urls.py** - reports URL include 추가

**templates/reports/** - 기본 보고서 템플릿 (기존 sub 레이아웃 패턴):
- total_data.html, coach_stats.html, attendance_report.html, monthly_stats.html
- 공통: 필터 폼 + 데이터 테이블 + 페이징 + Excel 다운로드 버튼

**접근 제어**: @login_required + staff 권한 체크 (is_staff)

### Step 6: 테이블 명세서 업데이트
- `python scripts/generate_table_spec.py` 실행

---

## 수정 파일 목록

| 파일 | 작업 |
|------|------|
| apps/enrollment/models.py | Attendance, ChangeHistory 모델 추가 |
| apps/enrollment/admin.py | Attendance, ChangeHistory Admin 추가 |
| apps/reports/models.py | 5개 리포트 모델 생성 |
| apps/reports/admin.py | 5개 모델 Admin 등록 |
| apps/reports/views.py | 보고서 뷰 8개 (목록 4 + Excel 4) |
| apps/reports/urls.py | URL 패턴 (신규) |
| config/urls.py | reports URL include 추가 |
| templates/reports/*.html | 보고서 템플릿 4개 |
| scripts/migrate_reports.py | 데이터 이관 스크립트 (신규) |

---

## 검증

1. `python manage.py makemigrations` → `python manage.py migrate` 성공
2. Django Admin에서 각 모델 조회 확인
3. `python scripts/migrate_reports.py` 실행 → 건수 검증:
   - Attendance: 231,147건
   - ChangeHistory: 877건
   - DailyTotalData: ~5,094,089건
   - DailyCoachData: 66,787건
   - DailyCoachDataNew: 574,419건
   - DailyCoachDataMonth: 42,785건
   - MonthlyData: 28,588건
4. 보고서 뷰 접속 → 필터링 → Excel 다운로드 정상 동작
5. 테이블 명세서 생성 확인
