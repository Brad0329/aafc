# Phase 8: 관리자 페이지 (ba_office 디자인 복제) 구현 계획

## Context
기존 ASP 관리자 페이지(ba_office)와 동일한 디자인/UX의 관리자 페이지를 Django로 구축한다.
기존 직원들이 재교육 없이 사용할 수 있도록 동일한 UI/메뉴/레이아웃을 유지한다.
Django 기본 Admin(/admin/)은 개발용으로 유지하고, 운영 관리자 페이지는 /ba_office/ 경로로 별도 구축한다.

## 규모 분석
- 기존 ASP ba_office: **328개 ASP 파일**, 14개 모듈, 100+ 이미지
- 9개 상단 메뉴: 시스템관리, 회원관리, 상담관리, 수강생관리, 과정관리, 출고관리, REPORT, 포탈관리, 쇼핑몰관리

## 서브 Phase 분할 (Phase 8을 8-1 ~ 8-10으로 분할)

| 서브Phase | 내용 | 주요 작업 |
|-----------|------|-----------|
| **8-1** | **기반 구축** | office 앱, OfficeUser 모델, CSS/JS/이미지 복사, base_office 템플릿, 로그인/로그아웃, 메인페이지 |
| **8-2** | **시스템관리** | 관리자 CRUD, 코드관리, 포인트설정, 관리자알림 |
| **8-3** | **회원관리** | 회원목록/상세, 자녀목록/상세, 회원통계, SMS, 포인트내역, 탈퇴회원 |
| **8-4** | **상담관리** | 상담목록/상세/답변, 상담등록, 권역설정, 무료체험 |
| **8-5** | **수강생관리** | 수강생목록/상세, 입단신청, 출결관리, 변경이력, 대기정보, 기본금액 |
| **8-6** | **과정관리** | 구장/코치/과정/훈련일정/프로모션 CRUD |
| **8-7** | **출고관리** | 출고요청/확인/완료, 용품설정 |
| **8-8** | **REPORT** | 주간보고, 전체DATA, 코치별통계, 출석현황, 월별통계 등 (기존 reports 앱 활용) |
| **8-9** | **포탈관리** | 팝업관리, 게시판관리(공지/이벤트/포토/학부모다이어리 등) |
| **8-10** | **쇼핑몰관리** | 카테고리/상품/주문/배송/재고 관리 |

---

## Phase 8-1: 기반 구축 (이번 세션)

### 1. office 앱 생성
- `apps/office/` 새 앱 생성
- models.py, views.py, urls.py, admin.py, forms.py, templatetags/

### 2. OfficeUser 모델 (`apps/office/models.py`)
기존 ASP `lf_officeuser` 테이블에서 마이그레이션:

```python
class OfficeUser(models.Model):
    office_code = models.AutoField(primary_key=True)
    office_name = models.CharField('표시명', max_length=20)
    office_realname = models.CharField('실명', max_length=20, blank=True)
    office_id = models.CharField('아이디', max_length=12, unique=True)
    office_pwd = models.CharField('비밀번호', max_length=200)
    office_part = models.CharField('부서명', max_length=50, blank=True)
    office_mail = models.CharField('이메일', max_length=100, blank=True)
    office_hp = models.CharField('연락처', max_length=20, blank=True)
    power_level = models.CharField('메뉴권한', max_length=20, blank=True)
    use_auth = models.CharField('접속구분', max_length=1, default='W')
    coach_code = models.CharField('코치코드', max_length=10, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)
```

권한 코드: A=시스템관리, M=회원관리, C=상담관리, H=수강생관리, L=과정관리, N=출고관리, R=REPORT, P=포탈관리, S=쇼핑몰관리

### 3. 정적 파일 복사
ASP → Django static 디렉토리로 복사:

```
c:\Users\user\Documents\2018_fcjunior\ba_office\css\     → static/ba_office/css/
c:\Users\user\Documents\2018_fcjunior\ba_office\js\      → static/ba_office/js/
c:\Users\user\Documents\2018_fcjunior\ba_office\images\  → static/ba_office/images/
(NanumGothic 폰트 파일 포함)
```

### 4. 템플릿 구조

**`templates/ba_office/base_office.html`** - 관리자 공통 레이아웃
- ASP의 top.asp + header.asp + bottom.asp 합친 구조
- CSS/JS includes (Style.css, jQuery 1.11.3, datepicker, ajax.js, date.js, table2excel.js)
- 헤더: 로고(aafc_emblem.png) + 사용자명 + 로그아웃 + GNB (권한별 메뉴)
- 사이드바: `{% block left_menu %}{% endblock %}`
- 콘텐츠: `{% block content %}{% endblock %}`
- 하단: viewport height 자동 조정 JS

**`templates/ba_office/login.html`** - 로그인 페이지 (base_office 비상속)
- 배경: bg_jinior.gif, 로그인박스: box_jnior.gif
- ID/PW 입력 + 로그인 버튼

**`templates/ba_office/main.html`** - 메인 대시보드
- 관리자 공지 목록 (OfficeNotification) - 클릭 시 펼치기/접기

**사이드바 include 패턴:**
```
templates/ba_office/includes/
  ├── manage_left.html      (시스템관리)
  ├── lfmember_left.html    (회원관리)
  ├── lfconsult_left.html   (상담관리)
  ├── lfstudent_left.html   (수강생관리)
  ├── lfclass_left.html     (과정관리)
  ├── release_left.html     (출고관리)
  ├── lfreport_left.html    (REPORT)
  ├── portal_left.html      (포탈관리)
  └── shop_left.html        (쇼핑몰관리)
```

### 5. 인증 시스템
- **세션 기반**: `request.session['office_user']` 에 OfficeUser 정보 저장
- **로그인**: /ba_office/login/ → office_id + office_pwd 검증 (SHA256 해시 비교)
- **로그아웃**: /ba_office/logout/ → 세션 삭제 + 로그인 리다이렉트
- **데코레이터**: `@office_login_required` - 세션 체크 + 로그인 리다이렉트
- **권한 체크**: `@office_permission_required('A')` - power_level에 해당 코드 포함 여부

### 6. URL 구조
```python
# config/urls.py에 추가
path('ba_office/', include('apps.office.urls')),

# apps/office/urls.py
urlpatterns = [
    path('', views.main_view, name='office_main'),
    path('login/', views.login_view, name='office_login'),
    path('logout/', views.logout_view, name='office_logout'),
]
```

### 7. 데이터 마이그레이션 스크립트
`scripts/migrate_office.py`:
- lf_officeuser → OfficeUser (관리자 사용자)
- lf_office_alim → OfficeNotification (이미 마이그레이션됨, 확인만)

### 8. 디자인 핵심 스펙
- **레이아웃**: 1200px 고정폭, 좌측메뉴 150px + 우측콘텐츠 1050px
- **헤더**: 높이 120px, 배경 top_bg.jpg, 하단 #002b69 2px 테두리
- **GNB**: NanumGothicExtraBold 16px, 흰색, hover시 #ffd736
- **좌측메뉴**: 배경 #4e4e4e, 텍스트 #4e4e4e, hover시 #d71921
- **테이블**: 상단 #d3a243 2px 테두리, 헤더 #f2f2f2 배경, 구분선 #d2d2d2
- **버튼**: 배경 #41404f, hover #9f9ea6, 또는 이미지 버튼(btn_*.gif)
- **페이징**: .paging 클래스, 중앙정렬
- **폰트**: NanumGothic, 기본 12px

---

## 수정할 파일 목록

### 새로 생성
- `apps/office/__init__.py`
- `apps/office/apps.py`
- `apps/office/models.py` (OfficeUser 모델)
- `apps/office/admin.py`
- `apps/office/views.py` (login, logout, main)
- `apps/office/urls.py`
- `apps/office/forms.py`
- `apps/office/decorators.py` (@office_login_required, @office_permission_required)
- `apps/office/context_processors.py` (office_user 정보 템플릿 전달)
- `templates/ba_office/base_office.html`
- `templates/ba_office/login.html`
- `templates/ba_office/main.html`
- `templates/ba_office/includes/manage_left.html`
- `templates/ba_office/includes/lfmember_left.html`
- `templates/ba_office/includes/lfconsult_left.html`
- `templates/ba_office/includes/lfstudent_left.html`
- `templates/ba_office/includes/lfclass_left.html`
- `templates/ba_office/includes/release_left.html`
- `templates/ba_office/includes/lfreport_left.html`
- `templates/ba_office/includes/portal_left.html`
- `templates/ba_office/includes/shop_left.html`
- `static/ba_office/css/` (ASP에서 복사)
- `static/ba_office/js/` (ASP에서 복사)
- `static/ba_office/images/` (ASP에서 복사)
- `scripts/migrate_office.py`

### 수정
- `config/settings/base.py` (INSTALLED_APPS에 office 추가, context_processors)
- `config/urls.py` (ba_office URL 추가)

---

## 검증 방법
1. `python manage.py makemigrations office && python manage.py migrate` - 마이그레이션 성공
2. `python scripts/migrate_office.py` - lf_officeuser 데이터 이관
3. 브라우저: http://localhost:8000/ba_office/ → 로그인 페이지 표시
4. 관리자 ID/PW로 로그인 → 메인 대시보드 + 관리자 공지 표시
5. 헤더 GNB 메뉴가 권한별로 표시/숨김 확인
6. 기존 ASP ba_office 화면과 시각적 1:1 비교
