# AAFC 시스템 마이그레이션 계획
## Classic ASP + MSSQL → Django + PostgreSQL

---

## Context

AAFC(유소년 축구 아카데미) 종합 관리 시스템을 운영 중인 회사가 자체 서버로 독립하려 한다. 현재 시스템은 Classic ASP(단종 기술) + MSSQL(유료) + Windows Server(유료)로 구성되어 유지보수가 어렵고 비용이 높다. 초보 프로그래머가 Claude AI와 함께 유지보수할 수 있도록 Python Django + PostgreSQL로 전환한다.

### 사용자 결정사항
- **배포**: 미정 (로컬 개발 우선, 추후 결정)
- **결제**: KCP + Toss 병행 유지
- **프론트엔드**: Django 템플릿 + jQuery

---

## 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.12+ |
| 프레임워크 | Django | 5.1+ |
| DB | PostgreSQL | 16+ |
| 프론트엔드 | Django Templates + jQuery 3.x | - |
| CSS | Bootstrap 5 + 기존 커스텀 CSS 활용 | - |
| 결제 | KCP Python SDK + Toss REST API | - |
| 에디터 | django-ckeditor-5 | - |
| 파일업로드 | Django 내장 + Pillow | - |
| SMS | django-sms 또는 직접 HTTP API | - |
| 인증 | Django Auth + NICE CheckPlus | - |
| 배포 | Gunicorn + Nginx + Let's Encrypt | - |
| 태스크큐 | Celery + Redis (SMS, 리포트 등) | - |

---

## Django 프로젝트 구조

```
aafc/                          # 프로젝트 루트
├── config/                    # 프로젝트 설정
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/              # 회원 (lf_member, lf_memberchild, lf_outmember)
│   ├── enrollment/            # 수강/입단 (lf_fcjoin_master, _course, _bill)
│   ├── courses/               # 강좌/구장/코치 (lf_lecture, lf_stadium, lf_coach)
│   ├── payments/              # 결제 (lf_pay_kcp, lf_pay_toslog, lf_paymethod)
│   ├── board/                 # 게시판 (lf_board, lf_boardcomment, lf_boardsub)
│   ├── consult/               # 상담 (lf_consult, lf_consult_free, lf_con_answer)
│   ├── shop/                  # 쇼핑몰 (lf_shop_goods, _order, _cart 등)
│   ├── points/                # 포인트 (lf_point_set, lf_userpoint_his)
│   ├── notifications/         # 알림/SMS (lf_alim, em_mmt_tran)
│   ├── reports/               # 리포트/통계 (lf_daily_*, lf_monthly_*)
│   └── common/                # 공통 코드 (lf_codegroup, lf_codesub, lf_setting)
├── templates/                 # HTML 템플릿
│   ├── base.html              # 공통 레이아웃 (header/footer)
│   ├── accounts/
│   ├── enrollment/
│   └── ...
├── static/                    # CSS, JS, 이미지
├── media/                     # 업로드 파일
├── scripts/                   # 데이터 마이그레이션 스크립트
└── manage.py
```

---

## 핵심 모델 설계 (앱별)

### accounts 앱
```
Member          ← lf_member (회원/학부모)
  - Django User 상속 (AbstractUser)
  - phone, address, sms_consent, mail_consent, status
  - SHA256 비밀번호: Django 커스텀 hasher로 호환

MemberChild     ← lf_memberchild (자녀)
  - FK → Member
  - name, birth, school, grade, height, weight, card_num
```

### enrollment 앱
```
Enrollment      ← lf_fcjoin_master (입단 마스터)
  - FK → Member, MemberChild, Lecture
  - apply_type (NEW/AGAIN/RENEW), lecture_status, pay_status
  - pay_price, pay_method, start_dt, end_dt

EnrollmentCourse ← lf_fcjoin_course (수강 과정 월별)
  - FK → Enrollment
  - course_ym, bill_code, course_status, course_ym_amt

EnrollmentBill   ← lf_fcjoin_bill (청구 내역)
  - FK → Enrollment
  - bill_code (1001~=수업료, 2001~=교육용품비), bill_amt

WaitStudent     ← lf_wait_student (대기자)
Attendance      ← lf_student_attendance (출석)
ChangeHistory   ← lf_change_history (변경이력)
```

### courses 앱
```
Stadium         ← lf_stadium (구장)
Coach           ← lf_coach (코치)
Lecture         ← lf_lecture (강좌)
  - FK → Stadium, Coach
  - title, class_type(pro/hobby), day, time, price, capacity
StadiumGoal     ← lf_stadium_goal (구장 목표)
Promotion       ← lf_promotion (프로모션)
```

### payments 앱
```
PaymentKCP      ← lf_pay_kcp + lf_pay_kcp_log (KCP 결제)
PaymentToss     ← lf_pay_toslog (Toss 결제)
PaymentFail     ← lf_pay_kcp_faillog (결제 실패)
```

### shop 앱
```
Category        ← lf_shop_category
Product         ← lf_shop_goods
ProductOption   ← lf_shop_goods_option + _item + _stock
Cart/CartItem   ← lf_shop_cart + _option
Order           ← lf_shop_order
OrderInfo       ← lf_shop_order_info + _option
OrderDelivery   ← lf_shop_order_delivery
```

### board, consult, points, notifications, reports, common
- 각각 해당 lf_* 테이블에 1:1 매핑
- common 앱: CodeGroup, CodeValue (lf_codegroup, lf_codesub), Setting (lf_setting)

---

## 마이그레이션 Phase 로드맵

### Phase 0: 프로젝트 세팅 + DB 마이그레이션 (1주)
**목표**: Django 프로젝트 생성, PostgreSQL에 데이터 이관

작업:
- [ ] Django 프로젝트 + 앱 스캐폴딩
- [ ] PostgreSQL 설치 및 DB 생성
- [ ] MSSQL → PostgreSQL 데이터 마이그레이션 스크립트 작성
  - mssql-django 또는 pyodbc로 MSSQL 읽기
  - Django ORM으로 PostgreSQL에 쓰기
  - 한글 인코딩 (UTF-8) 확인
  - 날짜 형식 변환 (MSSQL datetime → PostgreSQL timestamp)
- [ ] Django 커스텀 SHA256 hasher (기존 비밀번호 호환)
- [ ] 공통 코드 (lf_codegroup, lf_codesub) 마이그레이션

검증: `python manage.py shell`에서 Member.objects.count() == 10,150 확인

---

### Phase 1: 회원 + 인증 (2주)
**목표**: 회원가입, 로그인, 마이페이지 기본 동작

작업:
- [ ] accounts 앱: Member 모델 (AbstractUser 확장)
- [ ] MemberChild 모델
- [ ] 로그인/로그아웃 (Django auth + SHA256 커스텀 hasher)
- [ ] 회원가입 (NICE CheckPlus 연동은 추후, 일반 가입부터)
- [ ] 마이페이지: 프로필 수정, 자녀 관리
- [ ] 비밀번호 변경/찾기
- [ ] base.html 공통 레이아웃 (header/footer, 반응형)
- [ ] Django Admin: 회원 관리 기본 설정

검증: 브라우저에서 가입 → 로그인 → 마이페이지 접속 확인

---

### Phase 2: 강좌 + 구장 + 코치 (1주)
**목표**: 강좌/시설 정보 조회

작업:
- [ ] courses 앱: Stadium, Coach, Lecture 모델
- [ ] 구장 안내 페이지 (이미지맵 또는 리스트)
- [ ] 강좌 목록/상세 페이지
- [ ] 코칭스태프 소개 페이지
- [ ] AAFC 소개 페이지 (정적)
- [ ] Django Admin: 구장/코치/강좌 CRUD

검증: 구장 목록 → 강좌 조회 정상 동작

---

### Phase 3: 수강신청 + 결제 (3주) ★핵심
**목표**: 3단계 수강신청 플로우 + KCP/Toss 결제

작업:
- [ ] enrollment 앱: Enrollment, EnrollmentCourse, EnrollmentBill 모델
- [ ] 수강신청 Step 1: 자녀 선택 → 권역 → 구장 → 강좌 (AJAX cascade)
- [ ] 수강신청 Step 2: 과정 확인, 임시 저장
- [ ] 수강신청 Step 3: 결제 금액 계산 + 할인 적용
- [ ] payments 앱: KCP 결제 연동 (Python SDK/REST)
- [ ] payments 앱: Toss 결제 연동 (REST API)
- [ ] 결제 성공/실패 처리 + DB 상태 업데이트
- [ ] 결제 내역 조회 (마이페이지)
- [ ] Promotion 모델 + 할인 로직 (6종 할인)
- [ ] Django Admin: 수강생 관리, 입단 신청 관리

비즈니스 룰 (반드시 구현):
- 학부모(m_auth=P)만 수강신청 가능
- 동일 자녀 중복 수강신청 방지
- bill_code 체계: 1001~1099(수업료), 2001~2099(교육용품비)
- apply_gubun 판정: course_state 기반 NEW/AGAIN/RENEW
- 21일 이후 신청 시 익월 시작

검증: 수강신청 전체 플로우 → 결제 → 상태 변경 확인

---

### Phase 4: 게시판 + 상담 (1주)
**목표**: 커뮤니티 기능

작업:
- [ ] board 앱: Board, BoardComment, BoardFile 모델
- [ ] 게시판 유형별 목록/상세 (공지, 이벤트, 포토, U8/U10/U12 등)
- [ ] 글쓰기/수정 (CKEditor 5 연동)
- [ ] 댓글, 파일 첨부/다운로드
- [ ] consult 앱: 상담 신청, 무료체험 신청
- [ ] Django Admin: 게시판/상담 관리

검증: 글 작성 → 파일 첨부 → 댓글 → 상담 신청

---

### Phase 5: 쇼핑몰 (2주)
**목표**: 상품 카탈로그, 장바구니, 주문/결제

작업:
- [ ] shop 앱: Category, Product, ProductOption 모델
- [ ] 상품 목록/상세, 옵션 선택, 재고 확인
- [ ] 장바구니 (Cart, CartItem)
- [ ] 주문서 작성 → 결제 (payments 앱 재사용)
- [ ] 주문 내역 조회, 배송 추적
- [ ] Django Admin: 상품/주문/배송 관리

검증: 상품 선택 → 장바구니 → 주문 → 결제 → 주문 확인

---

### Phase 6: 포인트 + 알림 + SMS (1주)
**목표**: 부가 기능

작업:
- [ ] points 앱: PointConfig, PointHistory 모델
- [ ] 포인트 적립 로직 (hobby/pro, cycle/period 기반)
- [ ] 포인트 조회 (마이페이지)
- [ ] notifications 앱: 알림 모델
- [ ] SMS 발송 (Celery 태스크)
- [ ] Django Admin: 포인트 설정, SMS 발송

검증: 결제 시 포인트 자동 적립, SMS 발송 확인

---

### Phase 7: 리포트 + 관리자 고도화 (2주)
**목표**: 관리자 보고서, Excel 다운로드

작업:
- [ ] reports 앱: 주요 보고서 뷰 (전체 DATA, 결제 DATA, 출석 통계)
- [ ] Excel 다운로드 (openpyxl)
- [ ] 출석 관리 (관리자)
- [ ] 대기자 관리
- [ ] 코치별/구장별 통계
- [ ] Django Admin 커스터마이징 (권한 그룹 9개 매핑)

검증: 리포트 조회 → Excel 다운 → 데이터 정합성 확인

---

### Phase 8: NICE 본인인증 + 최종 마무리 (1주)
**목표**: 운영 준비 완료

작업:
- [ ] NICE CheckPlus 본인인증 연동 (회원가입)
- [ ] Daum 주소 검색 API 연동
- [ ] 메인 페이지 (슬라이더, 유튜브, 상담 폼)
- [ ] SEO + robots.txt + sitemap
- [ ] 보안 점검 (CSRF, XSS, SQL Injection - Django 기본 방어)
- [ ] 성능 테스트
- [ ] 서버 배포 (추후 결정된 환경에)

검증: 전체 기능 E2E 테스트, 기존 사이트와 비교 검증

---

## 데이터 마이그레이션 전략

### 접근 방식: Phase별 점진적 마이그레이션

```python
# scripts/migrate_data.py 구조
# 1. pyodbc로 MSSQL 연결 (localhost\SQLEXPRESS)
# 2. Django ORM으로 PostgreSQL에 쓰기
# 3. 테이블별 매핑 함수

def migrate_members():
    """lf_member → accounts.Member"""
    rows = mssql_cursor.execute("SELECT * FROM lf_member")
    for row in rows:
        Member.objects.create(
            username=row.member_id,
            password=f'sha256${row.member_pwd}',  # 커스텀 hasher
            name=row.member_name,
            phone=f'{row.mhtel1}-{row.mhtel2}-{row.mhtel3}',
            ...
        )
```

### 비밀번호 호환
```python
# config/hashers.py
class LegacySHA256Hasher(BasePasswordHasher):
    """기존 KISA SHA256 해시와 호환"""
    algorithm = 'sha256'

    def verify(self, password, encoded):
        _, hash_value = encoded.split('$', 1)
        return hashlib.sha256(password.encode()).hexdigest() == hash_value
```

### 주의사항
- 한글 인코딩: MSSQL은 CP949/UTF-8 혼용 가능 → UTF-8로 통일
- 날짜: MSSQL `GETDATE()` → PostgreSQL `NOW()`
- NULL 처리: `ISNULL()` → `COALESCE()`
- 외래키 순서: 부모 테이블 먼저 마이그레이션
- Soft delete: del_chk='Y' 레코드도 모두 이관

---

## 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| 결제 연동 장애 | 테스트 모드에서 충분히 검증 후 운영 전환 |
| 데이터 정합성 | 마이그레이션 후 row count + 금액 합계 교차 검증 |
| NICE 인증 실패 | Phase 8에서 처리, 그 전까지 일반 가입으로 대체 |
| 기존 사이트 중단 | 병행 운영: 새 시스템 안정화까지 기존 시스템 유지 |
| 성능 이슈 | 500만 건 daily_total_data 등 → DB 인덱스 + 페이지네이션 |

---

## 검증 방법

매 Phase 완료 시:
1. `python manage.py test` - 유닛 테스트 통과
2. 브라우저 E2E 테스트 - 주요 시나리오 수동 확인
3. 데이터 비교 - MSSQL vs PostgreSQL row count, 금액 합계 비교
4. 기존 사이트 화면과 비교 - 동일 기능 동작 확인

---

## 예상 일정

| Phase | 내용 | 기간 |
|-------|------|------|
| 0 | 프로젝트 세팅 + DB 마이그레이션 | 1주 |
| 1 | 회원 + 인증 | 2주 |
| 2 | 강좌 + 구장 + 코치 | 1주 |
| 3 | 수강신청 + 결제 ★ | 3주 |
| 4 | 게시판 + 상담 | 1주 |
| 5 | 쇼핑몰 | 2주 |
| 6 | 포인트 + 알림 + SMS | 1주 |
| 7 | 리포트 + 관리자 고도화 | 2주 |
| 8 | NICE 인증 + 최종 마무리 | 1주 |
| **합계** | | **약 14주** |

※ Claude와 함께 작업 시 실제 소요 시간은 상황에 따라 달라질 수 있음
