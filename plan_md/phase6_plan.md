# Phase 6: 포인트 + 알림 + SMS 구현 계획

## Context
Phase 5(쇼핑몰)까지 완료. Phase 6은 포인트 적립/사용 시스템, 알림장(코치→학부모), SMS 발송 로그를 구현한다.
MSSQL 소스: lf_point_set(10건), lf_userpoint_his(29,475건), lf_alim(352건), lf_office_alim(3건), em_mmt_tran_log_kyt(209,307건).

## 구현 범위
- **포인트**: 모델 + Admin + 마이포인트 페이지 + 쇼핑몰 결제 시 자동 적립 훅 + 데이터 이관
- **알림**: 모델 + Admin + 알림장 페이지 + 데이터 이관
- **SMS**: 로그 모델 + Admin(조회용) + 데이터 이관 (실제 SMS 발송은 Phase 8 관리자 페이지에서 구현)

---

## Step 1: 모델 + 마이그레이션

### 1-1. `apps/points/models.py` — PointConfig, PointHistory

**PointConfig** (lf_point_set, 10건):
| 필드 | 타입 | 설명 |
|------|------|------|
| point_seq | CharField(4), unique | 포인트코드 (101,102,201,301,401,501,601,602,701,801) |
| point_title | CharField(30) | 포인트명 |
| use_yn | CharField(2), default='Y' | 사용여부 |
| app_gbn | CharField(2), choices S/U | 적립(S)/사용(U) 구분 |
| save_gbn | CharField(2), choices PE/PO | 비율(PE)/정액(PO) |
| save_point | IntegerField, default=0 | 적립비율(%) 또는 정액(원) |
| limit_point | IntegerField, default=0 | 기준/최소금액 |

**PointHistory** (lf_userpoint_his, 29,475건):
| 필드 | 타입 | 설명 |
|------|------|------|
| point_dt | CharField(12) | 포인트일자 (YYYY-MM-DD) |
| member | FK→Member, to_field='username', db_column='member_id', SET_NULL | 회원 |
| member_name | CharField(20) | 회원명 |
| app_gbn | CharField(2), choices S/U | 적립/사용 |
| app_point | IntegerField | 포인트금액 |
| point_desc | CharField(200) | 내용 (수업료납부,쇼핑몰구매 등) |
| order_no | CharField(100) | 주문번호 |
| confirm_id | CharField(100) | 확인자/추천인ID |
| desc_detail | CharField(1000) | 상세내용 |
| insert_dt | DateTimeField, null=True | 등록일 |
| insert_id | CharField(20) | 등록자 |

### 1-2. `apps/notifications/models.py` — Notification, OfficeNotification, SMSLog

**Notification** (lf_alim, 352건):
| 필드 | 타입 | 설명 |
|------|------|------|
| no_seq | IntegerField, unique | 알림번호 |
| alim_gbn | CharField(1), default='P' | 알림구분 (P=학부모) |
| member | FK→Member, to_field='username', db_column='member_id', SET_NULL | 회원 |
| member_name | CharField(20) | 회원명 |
| child_id | CharField(16) | 자녀ID |
| local_code | IntegerField, null | 권역코드 |
| sta_code | IntegerField, null | 구장코드 |
| lecture_code | IntegerField, null | 강좌코드 |
| alim_title | CharField(100) | 제목 |
| alim_content | TextField | 내용 |
| alim_file | CharField(200) | 첨부파일 |
| del_chk | CharField(1), default='N' | 삭제여부 |
| insert_id | CharField(12) | 작성자ID |
| insert_name | CharField(20) | 작성자명 |
| insert_dt | DateTimeField, null | 등록일 |

**OfficeNotification** (lf_office_alim, 3건):
| 필드 | 타입 | 설명 |
|------|------|------|
| no_seq | IntegerField, unique | 알림번호 |
| atitle | CharField(100) | 제목 |
| acontent | TextField | 내용 |
| del_chk | CharField(1), default='N' | 삭제여부 |
| reg_dt | DateTimeField, null | 등록일 |
| reg_id | CharField(20) | 등록자 |

**SMSLog** (em_mmt_tran_log_kyt, 209,307건):
| 필드 | 타입 | 설명 |
|------|------|------|
| msg_key | CharField(20) | 메시지키 |
| date_client_req | DateTimeField, null | 발송요청일시 |
| subject | CharField(40) | 제목 |
| content | TextField | 내용 |
| callback | CharField(25) | 발신번호 |
| service_type | CharField(2), choices 0/2=SMS, 3=LMS | 서비스유형 |
| msg_status | CharField(1) | 발송상태 |
| recipient_num | CharField(25) | 수신번호 |
| broadcast_yn | CharField(1), default='N' | 대량발송여부 |
| date_sent | DateTimeField, null | 발송일시 |
| date_rslt | DateTimeField, null | 결과수신일시 |
| rslt | CharField(10) | 발송결과 |

### 1-3. makemigrations + migrate 실행

---

## Step 2: Admin

### 2-1. `apps/points/admin.py`
- PointConfigAdmin: list_display=[point_seq, point_title, use_yn, app_gbn, save_gbn, save_point, limit_point]
- PointHistoryAdmin: list_display=[id, point_dt, member, member_name, app_gbn, app_point, point_desc, insert_dt], list_filter=[app_gbn], search_fields=[member_id, member_name, point_desc]

### 2-2. `apps/notifications/admin.py`
- NotificationAdmin: list_display, list_filter=[alim_gbn, del_chk], search_fields
- OfficeNotificationAdmin: list_display, list_filter=[del_chk]
- SMSLogAdmin: list_display, list_filter=[service_type, msg_status], readonly_fields(전체)

---

## Step 3: 데이터 이관 스크립트

### 3-1. `scripts/migrate_points.py`
- migrate_shop.py 패턴 복제 (safe_str/checkint/make_aware 헬퍼)
- migrate_point_config(): lf_point_set → PointConfig (10건)
- migrate_point_history(): lf_userpoint_his → PointHistory (29,475건, 배치 100건)
  - app_point는 MSSQL varchar → int 변환 (checkint)
  - member FK 유효성 검사 (없으면 member=None으로 생성)

### 3-2. `scripts/migrate_notifications.py`
- migrate_notification(): lf_alim → Notification (352건)
- migrate_office_notification(): lf_office_alim → OfficeNotification (3건)
- migrate_sms_log(): em_mmt_tran_log_kyt → SMSLog (209,307건, 배치 500건)

---

## Step 4: URL 라우팅

### 4-1. `apps/points/urls.py` 생성
```
app_name = 'points'
path('mypoint/', views.point_list, name='point_list')
```

### 4-2. `apps/notifications/urls.py` 생성
```
app_name = 'notifications'
path('alim/', views.notification_list, name='notification_list')
```

### 4-3. `config/urls.py` 수정 — 2개 include 추가
```
path('points/', include('apps.points.urls')),
path('notifications/', include('apps.notifications.urls')),
```

---

## Step 5: Views + 유틸리티

### 5-1. `apps/points/views.py` — point_list
- @login_required
- 포인트 잔액 계산: SUM(case S) - SUM(case U) via aggregate
- 내역 목록 (최신순, 페이징)
- context: current_menu='mypoint', point_balance, page_obj

### 5-2. `apps/points/utils.py` — 포인트 유틸리티
- add_point_history(): 포인트 내역 등록 함수 (shop/enrollment에서 호출용)
- calculate_shop_point(settle_price): 쇼핑몰 구매 적립 포인트 계산 (PointConfig 601/602 기준)

### 5-3. `apps/notifications/views.py` — notification_list
- @login_required
- 해당 회원의 알림 목록 (alim_gbn='P', del_chk='N', 최신순)
- context: current_menu='alim', notifications

---

## Step 6: 템플릿

### 6-1. `templates/points/point_list.html`
- extends base.html, sub_top member, sub_menu(5개 항목), 브레드크럼
- 포인트 잔액 표시 섹션 (join_info 테이블)
- 포인트 내역 테이블: 일자, 구분(적립=파란/사용=빨강), 포인트, 내용
- 페이징 (payment_history.html 패턴 복제)

### 6-2. `templates/notifications/notification_list.html`
- extends base.html, sub_top member, sub_menu(5개 항목), 브레드크럼
- 알림 목록 테이블: 등록일, 제목, 작성자
- 내용 접기/펼치기 또는 바로 표시
- Empty state: "등록 알림글이 없습니다."

---

## Step 7: 메뉴 업데이트

### 7-1. `templates/base.html`
- PC gnb_menu (line 64-68): 마이포인트, 알림장 추가
- 모바일 메뉴 (line 122-126): 마이포인트, 알림장 추가

### 7-2. 마이페이지 sub_menu 통일 (4개 템플릿)
아래 파일들의 sub_menu를 5개 항목으로 확장:
- `templates/accounts/mypage.html` (line 9-14)
- `templates/enrollment/payment_history.html` (line 9-14)
- `templates/accounts/password_change.html` (line 9-14)
- `templates/accounts/profile_edit.html` (line 9-13)

```html
<li><a href="{% url 'accounts:mypage' %}">마이페이지</a></li>
<li><a href="{% url 'enrollment:payment_history' %}">결제내역</a></li>
<li><a href="{% url 'points:point_list' %}">마이포인트</a></li>
<li><a href="{% url 'notifications:notification_list' %}">알림장</a></li>
<li><a href="{% url 'accounts:password_change' %}">비밀번호 변경</a></li>
```

---

## Step 8: 쇼핑몰 결제 포인트 훅

### `apps/shop/views.py` shop_kcp_return (line 476 뒤)
- 결제 성공 후 포인트 적립: calculate_shop_point(settle_price) → add_point_history(app_gbn='S')
- use_cmoney > 0이면 포인트 사용: add_point_history(app_gbn='U')

---

## 수정 대상 파일 요약

| 파일 | 작업 |
|------|------|
| `apps/points/models.py` | PointConfig, PointHistory 모델 |
| `apps/points/admin.py` | Admin 등록 |
| `apps/points/views.py` | point_list 뷰 |
| `apps/points/utils.py` | add_point_history, calculate_shop_point (새 파일) |
| `apps/points/urls.py` | URL 패턴 (새 파일) |
| `apps/notifications/models.py` | Notification, OfficeNotification, SMSLog 모델 |
| `apps/notifications/admin.py` | Admin 등록 |
| `apps/notifications/views.py` | notification_list 뷰 |
| `apps/notifications/urls.py` | URL 패턴 (새 파일) |
| `config/urls.py` | points, notifications include 추가 |
| `templates/points/point_list.html` | 마이포인트 페이지 (새 파일) |
| `templates/notifications/notification_list.html` | 알림장 페이지 (새 파일) |
| `templates/base.html` | gnb_menu + 모바일 메뉴에 마이포인트/알림장 추가 |
| `templates/accounts/mypage.html` | sub_menu 5개로 확장 |
| `templates/enrollment/payment_history.html` | sub_menu 5개로 확장 |
| `templates/accounts/password_change.html` | sub_menu 5개로 확장 |
| `templates/accounts/profile_edit.html` | sub_menu 5개로 확장 |
| `apps/shop/views.py` | 결제 성공 시 포인트 적립/사용 훅 추가 |
| `scripts/migrate_points.py` | 포인트 데이터 이관 (새 파일) |
| `scripts/migrate_notifications.py` | 알림+SMS 데이터 이관 (새 파일) |

---

## 검증
1. Django Admin: 5개 모델 CRUD 확인
2. 데이터 건수: PointConfig=10, PointHistory≈29,475, Notification=352, OfficeNotification=3, SMSLog≈209,307
3. 브라우저: 로그인 → 마이아카데미 → 마이포인트 → 잔액/내역 표시 확인
4. 브라우저: 로그인 → 마이아카데미 → 알림장 → 알림 표시 확인
5. 메뉴: PC/모바일 네비게이션에 마이포인트/알림장 링크 확인
6. 쇼핑몰: 테스트 결제 → 포인트 자동 적립 확인
