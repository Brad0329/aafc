# Phase 1 구현 계획: 회원 + 인증

## 목표
회원가입, 로그인, 마이페이지 기본 동작 + 기존 ASP 사이트 디자인 적용

---

## 1. 모델 설계

### Member (AbstractUser 확장)
- MSSQL `lf_member` 테이블 매핑 (10,150건)
- Django AbstractUser 상속 → `first_name`, `last_name` 제거, `name` 필드 추가
- 주요 필드: member_code, name, tel, phone, email, zipcode, address1, address2
- 인증 관련: sms_consent, mail_consent, status, login_count, failed_count
- NICE 본인인증: join_ncsafe, birth, gender, join_safe_di, join_ipin_key, join_safegbn
- 기타: join_path, secession_desc, insert_dt
- `AUTH_USER_MODEL = 'accounts.Member'` 설정 필수

### MemberChild
- MSSQL `lf_memberchild` 테이블 매핑 (11,431건)
- FK → Member (to_field='username', db_column='member_id')
- 주요 필드: child_code, name, child_id, child_pwd, birth, gender
- 학교정보: school, grade, height, weight, size
- 상태: phone, login_count, status, last_login, course_state, card_num

### OutMember
- MSSQL `lf_outmember` 테이블 매핑 (35건)
- 단순 기록: member_id, member_name, out_desc, out_dt

---

## 2. 비밀번호 호환

- 기존 ASP: KISA SHA256 해시 (단순 SHA256, 솔트 없음)
- Django: `config/hashers.py`의 `LegacySHA256Hasher` 사용
- 이관 시 비밀번호 형식: `sha256$<해시값>`
- settings.py PASSWORD_HASHERS에 PBKDF2 + LegacySHA256 순서로 등록
- 기존 회원 로그인 시 자동으로 PBKDF2로 업그레이드됨

---

## 3. 데이터 이관

### 스크립트: `scripts/migrate_members.py`
- pyodbc로 MSSQL 연결 → Django ORM으로 PostgreSQL에 쓰기
- 전화번호 3분할(mhtel1/2/3) → 하이픈 결합(010-1234-5678)
- naive datetime → aware datetime 변환 (Asia/Seoul)
- member_status='D'인 회원 → is_active=False
- MemberChild: 부모 회원 존재 여부 확인 후 이관 (없으면 스킵)

### 주의사항
- AUTH_USER_MODEL 변경 시 DB 재생성 필요 (admin 마이그레이션 충돌)
- DB 재생성 후 공통코드 재이관 (`scripts/migrate_common.py`)
- superuser 재생성: admin / admin1234

---

## 4. 정적 파일 (기존 디자인 적용)

### 복사 대상 (2018_fcjunior → aafc/static/)
- `_css/` → `static/css/` (reset.css, common.css, index.css, sub.css, 폰트)
- `_js/` → `static/js/` (jQuery 1.11.3, flexslider, common.js, verification.js 등)
- `images/` → `static/images/` (로고, 아이콘, 배너, 서브페이지 이미지)

### Bootstrap 사용하지 않음
- 기존 사이트의 CSS 그대로 사용
- 기존 폼 레이아웃: `join_info` 테이블 기반

---

## 5. 템플릿 구조

### base.html (공통 레이아웃)
- 기존 ASP의 common.asp + header.asp + footer.asp 통합
- `{% load static %}` 사용
- 헤더: header_lnb (상단바) + header_gnb (GNB 메뉴) + 로고 + 모바일 헤더
- 푸터: 스폰서 로고 + 회사 정보
- QUICK MENU: 우측 사이드바
- 로그인 상태에 따라 "로그인/회원가입" ↔ "로그아웃/마이아카데미" 전환

### 서브페이지 공통 패턴
```html
<div id="sub_contents">
    <div class="sub_top member"><img src="..." alt=""/></div>   <!-- 상단 배너 -->
    <div class="sub_menu"><ul>...</ul></div>                      <!-- 탭 메뉴 -->
    <div class="sub_contents">
        <h2 class="sub_tit">제목<span>HOME > ...</span></h2>     <!-- 제목 + 경로 -->
        <h3 class="member_tit"><img .../>섹션제목</h3>             <!-- 섹션 헤더 -->
        <div class="join_info"><table>...</table></div>           <!-- 폼/정보 테이블 -->
        <div class="join_btn"><a href="...">...</a></div>         <!-- 버튼 -->
    </div>
</div>
```

---

## 6. URL 구조

| URL | 뷰 | 설명 |
|-----|-----|------|
| `/accounts/login/` | CustomLoginView | 로그인 |
| `/accounts/logout/` | logout_view | 로그아웃 |
| `/accounts/register/` | register_view | 회원가입 |
| `/accounts/mypage/` | mypage_view | 마이페이지 |
| `/accounts/profile/edit/` | profile_edit_view | 프로필 수정 |
| `/accounts/password/change/` | CustomPasswordChangeView | 비밀번호 변경 |
| `/accounts/child/add/` | child_add_view | 자녀 등록 |
| `/accounts/child/<pk>/edit/` | child_edit_view | 자녀 수정 |
| `/accounts/child/<pk>/delete/` | child_delete_view | 자녀 삭제 |

---

## 7. Forms

| 폼 클래스 | 용도 |
|-----------|------|
| LoginForm (AuthenticationForm) | 로그인 |
| RegisterForm (UserCreationForm) | 회원가입 |
| ProfileForm (ModelForm) | 프로필 수정 |
| MemberChildForm (ModelForm) | 자녀 등록/수정 |
| CustomPasswordChangeForm (PasswordChangeForm) | 비밀번호 변경 |

---

## 8. Django Admin

### MemberAdmin (UserAdmin 상속)
- list_display: username, name, phone, email, status, is_active, insert_dt
- search_fields: username, name, phone, email
- fieldsets: 개인정보, 주소, 동의/상태, 인증, 권한, 기타

### MemberChildAdmin
- list_display: name, parent, birth, school, grade, course_state, status
- raw_id_fields: parent

### OutMemberAdmin
- list_display: member_id, member_name, out_dt

---

## 9. Settings 변경사항

```python
# config/settings/base.py 추가
AUTH_USER_MODEL = 'accounts.Member'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
```

---

## 10. 생성/수정 파일 목록

| 파일 | 작업 |
|------|------|
| `apps/accounts/models.py` | Member, MemberChild, OutMember 모델 |
| `apps/accounts/forms.py` | 신규 - 5개 폼 클래스 |
| `apps/accounts/views.py` | 로그인, 회원가입, 마이페이지, 자녀 CRUD, 비밀번호 변경 |
| `apps/accounts/urls.py` | 신규 - URL 라우팅 |
| `apps/accounts/admin.py` | 회원/자녀/탈퇴회원 Admin |
| `apps/accounts/migrations/0001_initial.py` | 자동 생성 |
| `config/settings/base.py` | AUTH_USER_MODEL, LOGIN_URL 등 추가 |
| `config/urls.py` | accounts URL include 추가 |
| `scripts/migrate_members.py` | 신규 - 회원 데이터 이관 |
| `templates/base.html` | 신규 - 공통 레이아웃 (기존 디자인) |
| `templates/accounts/*.html` | 신규 - 7개 템플릿 |
| `static/css/`, `static/js/`, `static/images/` | 기존 ASP 사이트에서 복사 |
