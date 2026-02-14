# Phase 6: 포인트 + 알림 + SMS 테스트 체크리스트

## 서버 실행
```
python manage.py runserver
```

---

## 1. Django Admin 확인

- [ ] http://127.0.0.1:8000/admin/ 접속 (admin / admin1234)
- [ ] **포인트 설정 (PointConfig)**: 10건 확인
- [ ] **포인트 내역 (PointHistory)**: 29,475건 확인
- [ ] **알림장 (Notification)**: 352건 확인
- [ ] **사무실 알림 (OfficeNotification)**: 3건 확인
- [ ] **SMS 로그 (SMSLog)**: 209,307건 확인
- [ ] PointConfig 목록에서 적립/사용 구분, 비율/정액 방식 필터 동작
- [ ] PointHistory 목록에서 적립/사용 필터, 회원명/내용 검색 동작
- [ ] SMSLog 목록에서 서비스유형(SMS/LMS)/발송상태 필터 동작
- [ ] SMSLog 상세에서 모든 필드 readonly 확인

---

## 2. 마이포인트 페이지

> 로그인 필요 (포인트 내역이 있는 회원으로 로그인)

- [ ] http://127.0.0.1:8000/points/mypoint/ 접속
- [ ] 포인트 현황 표시 (보유 포인트, 총 적립, 총 사용)
- [ ] 보유 포인트 = 총 적립 - 총 사용 확인
- [ ] 포인트 내역 테이블 표시 (일자, 구분, 포인트, 내용)
- [ ] 적립 항목: 파란색 "+금액" 표시
- [ ] 사용 항목: 빨간색 "-금액" 표시
- [ ] 페이지네이션 동작 (20건 단위)
- [ ] 포인트 내역이 없는 회원: "포인트 내역이 없습니다." 표시

---

## 3. 알림장 페이지

> 로그인 필요 (알림이 있는 회원으로 로그인)

- [ ] http://127.0.0.1:8000/notifications/alim/ 접속
- [ ] 알림 목록 테이블 표시 (등록일, 제목, 작성자, 상태)
- [ ] 알림 행 클릭 시 내용 접기/펼치기 동작
- [ ] 삭제된 알림(del_chk='Y')은 표시되지 않음
- [ ] 알림이 없는 회원: "등록 알림글이 없습니다." 표시

---

## 4. 마이페이지 서브메뉴

- [ ] 마이페이지: 5개 메뉴 항목 표시 (마이페이지/결제내역/마이포인트/알림장/비밀번호 변경)
- [ ] 결제내역: 5개 메뉴 항목 표시
- [ ] 마이포인트: 5개 메뉴 항목 + "마이포인트" 활성(present) 표시
- [ ] 알림장: 5개 메뉴 항목 + "알림장" 활성(present) 표시
- [ ] 비밀번호 변경: 5개 메뉴 항목 표시
- [ ] 프로필 수정: 5개 메뉴 항목 표시

---

## 5. 네비게이션 메뉴

- [ ] 상단 GNB 메뉴 "마이아카데미" 하위에 "마이포인트" 링크 표시
- [ ] 상단 GNB 메뉴 "마이아카데미" 하위에 "알림장" 링크 표시
- [ ] 마이포인트 클릭 → /points/mypoint/ 이동
- [ ] 알림장 클릭 → /notifications/alim/ 이동
- [ ] 모바일 메뉴에서도 마이포인트/알림장 링크 동작

---

## 6. 쇼핑몰 포인트 적립 훅

> 쇼핑몰 테스트 결제 후 확인

- [ ] 쇼핑몰에서 상품 구매 완료 (테스트 결제)
- [ ] 결제 완료 후 마이포인트 페이지에서 "쇼핑몰구매" 적립 내역 확인
- [ ] 적립 포인트 = 결제금액의 1% (PointConfig 601/602 규칙 기준)
- [ ] use_cmoney(사용적립금) > 0인 경우 "쇼핑몰사용" 사용 내역 확인

---

## 7. 포인트 설정 확인 (Admin)

| point_seq | point_title | app_gbn | save_gbn | save_point | limit_point |
|-----------|-------------|---------|----------|------------|-------------|
| 101 | 정규반 주 1회 3개월 | S(적립) | PE(비율) | 1 | 0 |
| 102 | 정규반 주 2회 2,3개월 | S | PE | 1 | 0 |
| 201 | 클래식반 2개월 | S | PE | 1 | 0 |
| 301 | 친구추천 한 회원 | S | PO(정액) | 10000 | 0 |
| 401 | 친구추천 받은 회원 | N(미사용) | PO | 0 | 0 |
| 501 | 신규입단 | N | PO | 0 | 0 |
| 601 | 쇼핑몰구매 3만원 미만 | S | PE | 1 | 30000 |
| 602 | 쇼핑몰구매 3만원 이상 | S | PE | 1 | 30000 |
| 701 | 교육비 사용 | N | PO | 0 | 5000 |
| 801 | 쇼핑몰 사용 | S | PO | 0 | 5000 |

---

## 이관 데이터 건수 비교

| 테이블 | MSSQL | PostgreSQL | 비고 |
|--------|-------|------------|------|
| PointConfig (lf_point_set) | 10 | 10 | 일치 |
| PointHistory (lf_userpoint_his) | 29,475 | 29,475 | 일치 (member 미매칭 4건은 member=NULL로 이관) |
| Notification (lf_alim) | 352 | 352 | 일치 |
| OfficeNotification (lf_office_alim) | 3 | 3 | 일치 |
| SMSLog (em_mmt_tran_log_kyt) | 209,307 | 209,307 | 일치 |

---

## 생성/수정 파일 목록

| 파일 | 작업 |
|------|------|
| `apps/points/models.py` | PointConfig, PointHistory 모델 |
| `apps/points/admin.py` | Admin 설정 |
| `apps/points/views.py` | point_list 뷰 |
| `apps/points/utils.py` | add_point_history, calculate_shop_point (신규) |
| `apps/points/urls.py` | URL 패턴 (신규) |
| `apps/notifications/models.py` | Notification, OfficeNotification, SMSLog 모델 |
| `apps/notifications/admin.py` | Admin 설정 |
| `apps/notifications/views.py` | notification_list 뷰 |
| `apps/notifications/urls.py` | URL 패턴 (신규) |
| `config/urls.py` | points, notifications URL include 추가 |
| `templates/points/point_list.html` | 마이포인트 페이지 (신규) |
| `templates/notifications/notification_list.html` | 알림장 페이지 (신규) |
| `templates/base.html` | PC/모바일 GNB 메뉴에 마이포인트/알림장 추가 |
| `templates/accounts/mypage.html` | sub_menu 5개로 확장 |
| `templates/enrollment/payment_history.html` | sub_menu 5개로 확장 |
| `templates/accounts/password_change.html` | sub_menu 5개로 확장 |
| `templates/accounts/profile_edit.html` | sub_menu 5개로 확장 |
| `apps/shop/views.py` | 결제 성공 시 포인트 적립/사용 훅 추가 |
| `scripts/migrate_points.py` | 포인트 데이터 이관 스크립트 (신규) |
| `scripts/migrate_notifications.py` | 알림+SMS 데이터 이관 스크립트 (신규) |

---

## 참고: SMS 발송

현재 SMS는 발송 로그(SMSLog) 모델과 Admin 조회 기능만 구현되어 있습니다.
실제 SMS 발송 기능(발송 폼, 수신자 선택, 템플릿 관리)은 Phase 8 관리자 페이지(ba_office)에서 구현 예정입니다.
