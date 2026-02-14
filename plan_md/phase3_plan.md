# Phase 3 구현 계획: 수강신청 + 결제

## 목표
3단계 수강신청 플로우(자녀/강좌 선택 → 프로모션/할인 → 결제) + KCP 결제 연동 + 데이터 이관

---

## 1. 모델 설계

### Enrollment (lf_fcjoin_master → enrollment앱)
- FK → Member (to_field='username', db_column='member_id')
- FK → MemberChild (to_field='child_id', db_column='child_id')
- 결제: pay_stats, pay_method(max_length=10), pay_price, pay_dt
- 수강: lecture_stats, lec_cycle, lec_period, start_dt, end_dt
- 신청: apply_gubun(NEW/RE/RENEW/AGAIN), source_gubun, recommend_id
- 할인 6슬롯: discount1_id~discount6_id, discount1_price~discount6_price
- del_chk, insert_id, insert_dt

### EnrollmentCourse (lf_fcjoin_course)
- FK → Enrollment (db_column='no_seq')
- bill_code, course_ym(DateField), course_ym_amt, lecture_code, start_ymd, course_stats

### EnrollmentBill (lf_fcjoin_bill)
- FK → Enrollment (db_column='no_seq')
- bill_code, bill_desc, bill_amt, pay_stats, insert_id, insert_dt

### WaitStudent (lf_wait_student)
- local_code, sta_code, lecture_code, member_id, child_id, child_name
- wait_seq, trans_gbn, del_chk, insert_id, insert_dt

### PaymentKCP (lf_pay_kcp_log → payments앱)
- KCP 전 필드: req_tx, use_pay_method, bsucc, res_cd, res_msg, amount
- 주문: ordr_idxx, tno, good_mny, good_name
- 구매자: buyr_name, buyr_tel1, buyr_tel2, buyr_mail
- 카드: app_time, card_cd, card_name, app_no, noinf, quota
- 계좌: bank_name, bank_code, depositor, account, va_date
- 참조: pay_seq, member_num, pg_gbn, add_pnt, use_pnt, rsv_pnt

### PaymentFail (lf_pay_kcp_faillog)
- req_tx, use_pay_method, res_cd, res_msg, amount, ordr_idxx
- good_name, buyr_name, member_num, insert_dt

### LectureSelDay (lf_lecture_selday → courses앱 추가)
- lecture_code, syear, smonth, sday, admin_id
- unique_together: [lecture_code, syear, smonth, sday]

### PromotionMember (lf_promotion_member → courses앱 추가)
- coupon_uid, member_id, child_id, used, is_trash

### MemberChild 변경
- child_id 필드에 `unique=True` 추가 (FK 참조용)

---

## 2. 수강신청 3단계 플로우

### Step 1: 자녀선택 → 권역 → 구장 → 강좌 → 시작일
- 자녀 목록: MemberChild 조회 + 활성 수강 건수, 수강상태 표시
- 권역: CodeValue(grpcode='LOCD') 목록
- AJAX 캐스케이드: 권역→구장→강좌→시작일 순차 로드
- 정원 계산: EnrollmentCourse에서 현재 수강인원 카운트
- 상태 판단: jud=1(신청가능), jud=2(대기가능), jud=3(신청불가)
- 21일 규칙: 21일 이후면 익월, 아니면 당월 시작
- 추천인 확인: Member 존재 여부 AJAX 체크
- 대기 등록: 정원 초과 시 WaitStudent 생성

### Step 2: 프로모션/할인 확인
- Step 1 데이터를 POST로 수집 → Django session에 저장
- 강좌별 수업 횟수 계산: LectureSelDay에서 월별 카운트
- 금액 계산: lec_price × 수업횟수
- 6종 할인 AJAX 로드:
  1. 교육용품비 할인 (재입단 시 면제, 또는 프로모션 use_mode=1)
  2. 수강료 할인 (프로모션 use_mode=2)
  3. 결제금액 할인 (프로모션 use_mode=3)
  4. 3개월 선납 할인
  5. 피추천 할인
  6. 다회할인 (주2회→dc_2, 주3회→dc_3)

### Step 3: 결제 확인
- 할인 적용 후 최종 결제금액 계산
- KCP 가맹점 코드: sta_code=32 → 'AJVBN', 그 외 → 'A8BDH'
- 주문번호 생성: YYYYMMDDHHMMSS + username + '1' + child_id
- 테스트 모드: form이 직접 /payments/kcp/return/으로 POST

---

## 3. KCP 결제 처리

### kcp_return_view (payments/views.py)
- `@csrf_exempt @login_required`
- res_cd='0000' 성공 → `_create_enrollment()` 호출
- 실패 → `_create_fail_log()` + 실패 페이지

### _create_enrollment() (@transaction.atomic)
1. **Enrollment** 생성: 결제상태=PY, 수강상태=LY
2. **EnrollmentBill** 생성:
   - 1001: 수업료
   - 2001: 교육용품비 (금액 > 0일 때)
   - 2002: 교육용품할인 (음수)
   - 1003: 수강료할인, 결제금액할인 (음수)
   - 1004: 다회할인 (음수)
3. **EnrollmentCourse** 생성: 월별 × 강좌별 (lec_period × lecture_codes)
4. **MemberChild** 수강상태 → 'ING' 업데이트

### _create_payment_log()
- PaymentKCP 레코드 생성 (KCP POST 파라미터 저장)

### _create_fail_log()
- PaymentFail 레코드 생성

---

## 4. URL 구조

### enrollment앱 (apps/enrollment/urls.py)

| URL | 뷰 | 설명 |
|-----|-----|------|
| `/enrollment/apply/` | apply_step1_view | Step 1 |
| `/enrollment/api/stadiums/` | ajax_load_stadiums | AJAX: 구장 목록 |
| `/enrollment/api/lectures/` | ajax_load_lectures | AJAX: 강좌 목록 |
| `/enrollment/api/course-days/` | ajax_course_days | AJAX: 수업일 |
| `/enrollment/api/recommend-check/` | ajax_recommend_check | AJAX: 추천인 확인 |
| `/enrollment/api/waitlist-add/` | ajax_waitlist_add | AJAX: 대기 등록 |
| `/enrollment/apply/step2/` | apply_step2_view | Step 2 |
| `/enrollment/api/promotions/` | ajax_load_promotions | AJAX: 프로모션 |
| `/enrollment/apply/step3/` | apply_step3_view | Step 3 |
| `/enrollment/payment-history/` | payment_history_view | 결제내역 |

### payments앱 (apps/payments/urls.py)

| URL | 뷰 | 설명 |
|-----|-----|------|
| `/payments/kcp/return/` | kcp_return_view | KCP 결제 콜백 |

---

## 5. 템플릿

| 파일 | 설명 |
|------|------|
| `enrollment/apply_step1.html` | Step 1: jQuery AJAX 캐스케이드 ($.load, $.ajax) |
| `enrollment/apply_step2.html` | Step 2: 프로모션 AJAX 로드 |
| `enrollment/apply_step3.html` | Step 3: KCP form (테스트모드: 직접 submit) |
| `enrollment/fragments/stadium_list.html` | 구장 라디오 버튼 |
| `enrollment/fragments/lecture_list.html` | 강좌 체크박스 테이블 (jud 상태 표시) |
| `enrollment/fragments/course_days.html` | 시작일 라디오 버튼 |
| `enrollment/fragments/promotion_list.html` | 할인 6종 테이블 |
| `enrollment/payment_history.html` | 결제내역 목록 (페이지네이션) |
| `payments/payment_success.html` | 결제 성공 페이지 |
| `payments/payment_fail.html` | 결제 실패 페이지 |

---

## 6. 세션 기반 데이터 전달

- 레거시 ASP의 `lf_mobile_temppay` 테이블 대신 Django session 사용
- `request.session['enrollment_data']` 키에 딕셔너리 저장
- Step 1 → Step 2: child_id, local_code, sta_code, lecture_codes, start_days, sym 등
- Step 2 → Step 3: 위 + 할인 금액/ID, payment_price, order_idxx, good_name
- 결제 완료 후 세션에서 삭제

---

## 7. 데이터 이관

### 스크립트: `scripts/migrate_enrollment.py`
- pyodbc로 MSSQL 연결 → Django ORM으로 PostgreSQL에 쓰기
- 이관 순서 (의존성): LectureSelDay → PromotionMember → Enrollment → EnrollmentBill → EnrollmentCourse → WaitStudent → PaymentKCP → PaymentFail

### 이관 결과
| 테이블 | 건수 |
|--------|------|
| LectureSelDay | 196,609 |
| PromotionMember | 0 (테이블 없음, 스킵) |
| Enrollment | 79,490 |
| EnrollmentBill | 131,280 |
| EnrollmentCourse | 220,596 |
| WaitStudent | 107 |
| PaymentKCP | 42,721 |
| PaymentFail | 1,138 |

### 주의사항
- Enrollment PK 보존 (id=no_seq) → FK 무결성 유지
- MSSQL `pay_method`에 BENEFIT/ZEROPAY(7자) 존재 → max_length=5에서 10으로 확대
- MSSQL `discount_id/discount_price`(단수) → Django `discount1_id/discount1_price`에만 매핑
- `lf_wait_student`에 `insert_dt` 컬럼 없음 → auto_now_add 사용
- `lf_promotion_member` 테이블 없음 → try/except로 스킵
- Enrollment.child FK를 위해 MemberChild.child_id에 unique=True 필요

---

## 8. Django Admin

### EnrollmentAdmin
- list_display: id, member, child, pay_stats, pay_price, lecture_stats, insert_dt
- search_fields: member_id, child_id
- list_filter: pay_stats, lecture_stats, apply_gubun
- inlines: EnrollmentBillInline, EnrollmentCourseInline

### WaitStudentAdmin
- list_display: child_name, lecture_code, wait_seq, trans_gbn

### PaymentKCPAdmin
- list_display: ordr_idxx, amount, res_cd, buyr_name, insert_dt
- search_fields: ordr_idxx, buyr_name, member_num

### PaymentFailAdmin
- list_display: ordr_idxx, amount, res_cd, res_msg, insert_dt

### LectureSelDayAdmin / PromotionMemberAdmin
- courses앱 Admin에 추가

---

## 9. 네비게이션 업데이트

### base.html 변경
- PC GNB: "입단신청" href → `{% url 'enrollment:apply_step1' %}`
- PC GNB: "마이아카데미" 드롭다운 추가 (마이페이지, 결제내역, 비밀번호 변경)
- 모바일 메뉴: 동일하게 입단신청 링크 + 마이아카데미 하위 결제내역
- QUICK MENU: 입단신청 아이콘 링크

### 서브메뉴 업데이트 (마이아카데미 하위 페이지)
- accounts/mypage.html: "마이페이지 | 결제내역 | 비밀번호 변경"
- accounts/password_change.html: 동일

---

## 10. 생성/수정 파일 목록

| 파일 | 작업 |
|------|------|
| `apps/enrollment/models.py` | Enrollment, EnrollmentCourse, EnrollmentBill, WaitStudent |
| `apps/enrollment/views.py` | Step 1~3 뷰 + AJAX 6개 + 결제내역 (~570줄) |
| `apps/enrollment/urls.py` | 신규 - 10개 URL 패턴 |
| `apps/enrollment/admin.py` | EnrollmentAdmin(인라인), WaitStudentAdmin |
| `apps/payments/models.py` | PaymentKCP, PaymentFail |
| `apps/payments/views.py` | kcp_return_view + _create_enrollment (~292줄) |
| `apps/payments/urls.py` | 신규 - 1개 URL 패턴 |
| `apps/payments/admin.py` | PaymentKCPAdmin, PaymentFailAdmin |
| `apps/courses/models.py` | LectureSelDay, PromotionMember 추가 |
| `apps/courses/admin.py` | LectureSelDayAdmin, PromotionMemberAdmin 추가 |
| `apps/accounts/models.py` | MemberChild.child_id에 unique=True |
| `config/urls.py` | enrollment, payments URL include 추가 |
| `templates/base.html` | 입단신청 링크, 마이아카데미 드롭다운, 퀵메뉴 |
| `templates/accounts/mypage.html` | 서브메뉴에 결제내역 추가 |
| `templates/accounts/password_change.html` | 서브메뉴에 결제내역 추가 |
| `templates/enrollment/*.html` | 신규 - 8개 템플릿 |
| `templates/payments/*.html` | 신규 - 2개 템플릿 |
| `scripts/migrate_enrollment.py` | 신규 - 8개 테이블 이관 (~447줄) |
