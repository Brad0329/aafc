# AAFC 시스템 구조서

> 최종 수정: 2026-04-16
> 유소년 축구 아카데미(AAFC) 종합 관리 시스템

---

## 1. 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.12 |
| 프레임워크 | Django | 5.1 |
| DB | PostgreSQL | 16 (로컬) / 17 (AWS RDS) |
| 프론트엔드 | Django Templates + jQuery 3.x | - |
| CSS | 기존 ASP 사이트 커스텀 CSS (Bootstrap 미사용) | - |
| 결제 | KCP Python SDK | - |
| 에디터 | CKEditor 4 (관리자) / CKEditor 5 (프론트) | 4.22.1 / 41.4.2 |
| 인증 | Django Auth (프론트) + 세션 기반 (관리자) | - |
| 배포 | Gunicorn + Nginx + EC2 + RDS + S3 | - |
| 설정 파일 | config/settings/base.py, local.py, prod.py | - |

---

## 2. 프로젝트 구조

```
aafc/
├── config/                     # 프로젝트 설정
│   ├── settings/
│   │   ├── base.py             # 공통 설정
│   │   ├── local.py            # 로컬 개발 (PostgreSQL localhost)
│   │   └── prod.py             # 운영 (RDS)
│   ├── urls.py                 # 최상위 URL 라우팅
│   ├── views.py                # 메인페이지, robots.txt, sitemap
│   └── wsgi.py
├── apps/                       # 12개 앱
│   ├── accounts/               # 회원/자녀/탈퇴회원 (3 모델)
│   ├── enrollment/             # 수강신청/과정/청구/출석/대기자 (7 모델)
│   ├── courses/                # 구장/코치/강좌/프로모션/훈련일정 (9 모델)
│   ├── payments/               # KCP 결제/실패로그 (2 모델)
│   ├── board/                  # 게시판/댓글/첨부파일/팝업 (4 모델)
│   ├── consult/                # 상담/답변/무료체험/권역 (4 모델)
│   ├── shop/                   # 쇼핑몰 전체 (12 모델)
│   ├── points/                 # 포인트설정/내역 (2 모델)
│   ├── notifications/          # 알림/관리자알림/SMS로그 (3 모델)
│   ├── reports/                # 월별데이터 (1 모델)
│   ├── common/                 # 공통코드/설정 (3 모델)
│   └── office/                 # 관리자 페이지 (2 모델, 173 URL)
├── templates/                  # HTML 템플릿
│   ├── base.html               # 프론트 공통 레이아웃
│   ├── accounts/
│   ├── ba_office/              # 관리자 페이지 템플릿
│   ├── board/
│   ├── consult/
│   ├── courses/
│   ├── enrollment/
│   ├── notifications/
│   ├── payments/
│   ├── points/
│   └── shop/
├── static/
│   ├── css/                    # reset.css, common.css, index.css, sub.css
│   ├── js/
│   ├── images/
│   └── ba_office/              # 관리자 전용 CSS/JS/이미지
├── media/                      # 업로드 파일 (운영: S3)
│   └── fcdata/                 # 게시판/쇼핑몰/팝업 이미지
├── scripts/                    # MSSQL→PostgreSQL 마이그레이션 스크립트 14개
└── manage.py
```

**전체 통계**: 모델 52개, URL 224개 (프론트 51 + 관리자 173), 앱 12개

---

## 3. 앱별 모델 목록

### accounts (회원)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Member** | 회원/학부모 (AbstractUser) | username(=member_id), name, tel, phone, zipcode, address1, address2, birth, gender, sms_consent, status | AUTH_USER_MODEL |
| **MemberChild** | 자녀 | child_id(unique), name, birth, gender, school, grade, phone, course_state | parent → Member (to_field='username') |
| **OutMember** | 탈퇴회원 | member_id, member_name, out_desc, out_dt | 없음 |

### enrollment (수강신청)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Enrollment** | 입단 마스터 | pay_stats, pay_method, pay_price, lecture_stats, lec_cycle, lec_period, start_dt, end_dt, apply_gubun(NEW/RE/RENEW/AGAIN), discount1~6, cancel_code/desc/date, shuttle_yn | member → Member, child → MemberChild |
| **EnrollmentCourse** | 수강 과정 (월별) | bill_code, course_ym, course_ym_amt, lecture_code(IntegerField), course_stats | enrollment → Enrollment |
| **EnrollmentBill** | 청구 내역 | bill_code(1001~=수업료, 2001~=교육용품비), bill_desc, bill_amt, pay_stats | enrollment → Enrollment |
| **Attendance** | 출석 | local_code, sta_code, lecture_code, child_id, attendance_dt, attendance_gbn, app_month | 없음 (코드값 참조) |
| **ChangeHistory** | 변경이력 | member_id, child_id, chg_gbn, chg_desc, no_seq, src_seq | 없음 |
| **WaitStudent** | 대기자 | local_code, sta_code, lecture_code, member_id, child_id, trans_gbn, bigo, phone | 없음 |
| **EnrollmentCourseSrc** | 과정 원본 | src_seq, pknum, no_seq, bill_code, course_ym, lecture_code, ch_name | 없음 |

> **주의**: EnrollmentCourse.lecture_code는 IntegerField(FK 아님) → Lecture 수동 조회 필요

### courses (강좌/구장/코치)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Stadium** | 구장 | sta_code(unique), local_code, sta_name, sta_nickname, use_gbn | 없음 |
| **Coach** | 코치 | coach_code(unique), coach_name, coach_level, phone, use_gbn | 없음 |
| **StadiumCoach** | 구장-코치 매핑 | unique_together: [stadium, coach] | stadium → Stadium, coach → Coach |
| **Lecture** | 강좌 | lecture_code(unique), local_code, lecture_title, lecture_day, lecture_time, class_gbn, lec_price, stu_cnt | stadium → Stadium, coach → Coach, t_coach → Coach |
| **StadiumGoal** | 구장 목표 | sta_year, sta_month, sta_goal | stadium → Stadium |
| **Promotion** | 프로모션 | uid(unique), kind, title, discount, discount_unit, is_use, local_code, sta_code | 없음 |
| **LectureSelDay** | 수업일정 | lecture_code, syear, smonth, sday | 없음 |
| **PromotionMember** | 프로모션 사용자 | coupon_uid, member_id, child_id, used | 없음 |
| **LectureTraining** | 훈련일정 | sta_code, local_code, training_dt, training_desc | 없음 |

### payments (결제)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **PaymentKCP** | KCP 결제 | req_tx, use_pay_method, res_cd, amount, ordr_idxx, tno, good_mny, buyr_name, card_cd, app_no, pay_seq | 없음 |
| **PaymentFail** | 결제 실패 | req_tx, res_cd, res_msg, amount, ordr_idxx | 없음 |

### board (게시판)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Board** | 게시판 | b_seq(unique), b_gbn(Y=공지/N=소식/E=이벤트/P=포토/PR=학부모다이어리/ST=공부하는AAFC/U8/U10/U12=클래식반), b_title, b_content, b_hit, b_notice_yn, del_chk | 없음 |
| **BoardComment** | 댓글 | b_gbn, comment, insert_name, del_chk | board → Board (to_field='b_seq') |
| **BoardFile** | 첨부파일 | bs_img, bs_thumimg, bs_file, bs_downcnt | board → Board (to_field='b_seq') |
| **Popup** | 팝업 | pop_title, pop_begin_date, pop_end_date, pop_img, pop_url, pop_width/height, pop_yn | 없음 |

### consult (상담)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Consult** | 상담 | member_id, child_id, consult_name, consult_tel, consult_title, consult_content, local_code, sta_code | 없음 |
| **ConsultAnswer** | 상담 답변 | consult_category, consult_answer, coach_code | consult → Consult |
| **ConsultFree** | 무료체험 | jname, jphone1/2/3, jlocal, confirm_yn, del_chk | 없음 |
| **ConsultRegion** | 상담 권역 | reg_gbn, reg_name, mphone, del_chk | 없음 |

### shop (쇼핑몰)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Category** | 카테고리 | cate_code(unique), cate_name, cate_depth, cate_parent | 없음 |
| **Product** | 상품 | gd_code(unique), gd_name, gd_price, gd_option_kind, gd_is_soldout | category → Category |
| **ProductOption** | 상품 옵션 | opt_name, opt_items, opt_is_require | product → Product |
| **ProductOptionItem** | 옵션 항목 | opt_item, opt_price, opt_sort | option → ProductOption |
| **ProductOptionStock** | 옵션별 재고 | opt_item_idx1, opt_item_idx2, opt_stock | product → Product |
| **Cart** | 장바구니 | ea, option_kind, option_txt | member → Member, product → Product |
| **CartOption** | 장바구니 옵션 | option_title, option_item, option_price | cart → Cart |
| **Order** | 주문 | order_no(unique), payway, total_price, settle_price, state, is_finish | member → Member |
| **OrderItem** | 주문 상품 | goods_uid, goods_title, price, ea | order → Order |
| **OrderItemOption** | 주문 옵션 | title, item, price | order_item → OrderItem |
| **OrderDelivery** | 배송 | delivery_name, delivery_no, delivery_fee, is_delivery | order → Order |
| **ShopPaymentKCP** | 쇼핑몰 KCP 결제 | use_pay_method, res_cd, tno, amount, card_cd, app_no | order → Order |

### points (포인트)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **PointConfig** | 적립 규칙 | point_seq(unique), point_title, app_gbn(PE=비율/PO=정액), save_point, use_yn | 없음 |
| **PointHistory** | 포인트 내역 | point_dt, member_name, app_gbn(S=적립/U=사용), app_point, point_desc, order_no | member → Member |

> **잔액 계산**: SUM(app_gbn='S') - SUM(app_gbn='U')

### notifications (알림/SMS)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **Notification** | 코치→학부모 알림 | no_seq(unique), alim_gbn, child_id, alim_title, alim_content, lecture_code | member → Member |
| **OfficeNotification** | 관리자 알림 | no_seq(unique), atitle, acontent, del_chk | 없음 |
| **SMSLog** | SMS 발송 로그 | msg_key, subject, content, callback, recipient_num, rslt | 없음 |

### reports (리포트)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **MonthlyData** | 월별 통계 | proc_dt, sta_name, sta_code, m_cnt, goal_cnt, newT/F_appl_cnt, renewT/F_appl_cnt | 없음 |

> DailyTotalData, DailyCoachData 등 4개 집계 모델은 제거됨 → Enrollment 원본 직접 조회로 전환

### common (공통)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **CodeGroup** | 코드 그룹 | grpcode(PK), grpcode_name | 없음 |
| **CodeValue** | 코드 값 | subcode, code_name, code_desc, code_order | group → CodeGroup |
| **Setting** | 시스템 설정 | join_price, pk_price | 없음 |

### office (관리자)

| 모델 | 설명 | 주요 필드 | FK |
|------|------|----------|-----|
| **OfficeUser** | 관리자 계정 | office_id(unique), office_name, office_pwd(SHA256), power_level, use_auth, coach_code | 없음 |
| **OfficeLoginHistory** | 로그인 이력 | office_id, action, memo, login_dt, login_ip | 없음 |

> **권한 코드** (use_auth): A=시스템관리, M=회원관리, C=상담관리, H=수강생관리, L=과정관리, N=출고관리, R=REPORT, G=매출정보, P=포탈관리, S=쇼핑몰관리

---

## 4. 인증 체계

### 프론트 (회원)
- Django Auth 기반 (`AUTH_USER_MODEL = 'accounts.Member'`)
- AbstractUser 상속, username = member_id
- 비밀번호: SHA256 커스텀 hasher (`config/hashers.py`) - 기존 ASP 시스템 호환
- 로그인: `@login_required` 데코레이터

### 관리자 (ba_office)
- 별도 세션 기반 (`request.session['office_user']`)
- OfficeUser 모델, SHA256 해시
- `@office_login_required` + `@office_permission_required('코드')` 데코레이터
- Nginx IP 제한 적용

---

## 5. 주요 비즈니스 플로우

### 수강신청 (enrollment)
```
Step1: 자녀 선택 → 권역 → 구장 → 강좌 → 시작일 (AJAX cascade)
Step2: 프로모션/할인 6종 적용 (추천인/다회/프로모션/재학생 등)
Step3: 결제 확인 + KCP 결제
→ 결제 성공 시: Enrollment + EnrollmentBill + EnrollmentCourse + PaymentKCP 생성 (@transaction.atomic)
→ 세션 기반 Step간 데이터 전달
```

### 쇼핑몰 주문 (shop)
```
상품 목록(카테고리탭) → 상품 상세(옵션선택) → 장바구니 → 주문서(주문자/수령인/배송/결제) → KCP 결제 → 주문조회
→ 결제 성공 시: 포인트 자동 적립/사용 (points.utils)
```

### 관리자 수강생 등록 (office)
```
자녀 검색(AJAX) → 권역 → 구장 → 강좌(AJAX) → 금액 계산 → 등록
→ bill_code 체계: 1001(수업료), 1002(첫달차감), 1003(할인), 1006(피추천인), 1007(다회), 1009(차량), 2001(교육용품비), 2002(교육용품할인)
→ 재학생(ING/END/PAU) → 교육용품비 자동 0원
```

### 관리자 일괄처리 (office)
```
student_list 체크박스 → procsel 드롭다운 선택:
D=익월수강예정, DN=개월선택재수강, Y=수강확정, T=수강확정+결제완료, L=결제안내LMS
→ 자동이체 methods (MUCU/MCDO/SDM/TA/CAU/YDP): pay_stats='PY', lecture_stats='LY' 자동 설정
```

### 포인트 적립/사용 (points)
```
적립 규칙: PointConfig (PE=비율%, PO=정액)
잔액 = SUM(app_gbn='S') - SUM(app_gbn='U')
쇼핑몰 결제 성공 시 자동 적립 (points.utils.calculate_shop_point, add_point_history)
```

---

## 6. URL 구조

### 프론트 (51개)

| prefix | 앱 | URL 수 | 주요 페이지 |
|--------|-----|--------|------------|
| `/` | config | 1 | 메인페이지 |
| `/accounts/` | accounts | 9 | 회원가입, 로그인, 마이페이지, 자녀관리, 비밀번호변경 |
| `/academy/` | courses | 8 | 구장안내, 코칭스태프, 강좌목록, 운영진인사말 |
| `/enrollment/` | enrollment | 10 | 수강신청 Step1~3, 결제내역, AJAX(구장/강좌/수업일) |
| `/payments/` | payments | 1 | KCP 결제 콜백 |
| `/board/` | board | 7 | 게시판 목록/상세/글쓰기/수정/삭제, 댓글 |
| `/consult/` | consult | 3 | 상담신청, 무료체험, AJAX 구장검색 |
| `/shop/` | shop | 11 | 상품목록/상세, 장바구니, 주문서, 결제, 주문조회 |
| `/points/` | points | 1 | 마이포인트 |
| `/notifications/` | notifications | 1 | 알림장 |

### 관리자 `/ba_office/` (173개)

| 메뉴 | 뷰 파일 | 주요 기능 |
|------|---------|----------|
| 시스템관리 | views.py | 관리자 CRUD, 코드관리, 포인트설정, 관리자알림 |
| 회원관리 | views.py | 회원 CRUD, 자녀 CRUD, 회원통계, SMS, 포인트내역, 탈퇴회원 |
| 상담관리 | views.py | 상담 리스트/상세/등록/답변, 권역설정, 무료체험 |
| 수강생관리 | views.py | 수강생 조회/상세/등록, 입단신청, 변경이력, 출결, 일괄처리, 대기자 |
| 과정관리 | views.py | 구장/코치/강좌 관리, 훈련일정, 프로모션 |
| REPORT | views_report.py | 22개 리포트 (결제/코치별/출석/월별 등), Excel 다운로드 |
| 포탈관리 | views_portal.py | 팝업관리, 게시판관리 (공지/이벤트/포토 등) |
| 쇼핑몰관리 | views_shop.py | 카테고리/상품/주문/배송리포트/통합재고 |
| 출고관리 | - | 보류 (미구현) |

---

## 7. 외부 연동

| 연동 | 용도 | 비고 |
|------|------|------|
| **KCP** | 수강신청 + 쇼핑몰 결제 | 테스트모드 (state=200, is_finish='T' 직접 설정) |
| **Daum Postcode API** | 주소검색 | 회원가입, 주문서 |
| **CKEditor 4** (CDN) | 관리자 게시판 에디터 | 4.22.1 |
| **CKEditor 5** (CDN) | 프론트 게시판 에디터 | 41.4.2, django-ckeditor-5 설치됨 |

---

## 8. 주요 주의사항

### 모델 필드명

| 흔한 실수 | 실제 필드명 |
|-----------|------------|
| member.m_name | member.**name** |
| member.m_email | member.**email** |
| member.m_zip | member.**zipcode** |
| member.m_address | member.**address1** / **address2** |
| child.child_name | child.**name** |
| child.del_chk | child.**status** |
| child.member (FK) | child.**parent** |
| child.sch_name | child.**school** |
| child.sch_grade | child.**grade** |
| child.sex | child.**gender** |
| enrollment.lecture_status | enrollment.**lecture_stats** |
| enrollment.pay_status | enrollment.**pay_stats** |
| enrollment.apply_type | enrollment.**apply_gubun** |
| enrollmentcourse.course_status | enrollmentcourse.**course_stats** |

### FK 관계 주의

- Member FK 참조: `to_field='username'` (not pk)
- MemberChild FK 참조: `to_field='child_id'` (not pk)
- EnrollmentCourse.lecture_code: **IntegerField** (FK 아님) → Lecture 수동 조회 필요
- Board FK 참조: `to_field='b_seq'` (not pk)

### 기타

- Django `stringformat` 필터는 천단위 콤마 미지원 → `humanize`의 `intcomma` 사용 (`{% load humanize %}` 필수)
- MemberChild에 child_id가 빈 레코드 존재 → 템플릿에서 `{% if c.child_id %}` 방어 필요
- MSSQL 필드 길이가 Django 모델보다 긴 경우 있음 (예: pay_method에 BENEFIT/ZEROPAY 등 7자)
- 딕셔너리를 템플릿에서 변수 키로 조회 불가 → 뷰에서 객체에 속성 직접 부여 필요
- 관리자 URL prefix: `/ba_office/` (config/urls.py에서 설정)
