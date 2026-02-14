# Phase 2 구현 계획: 강좌 + 구장 + 코치

## 목표
구장 안내, 코칭스태프 소개, 교육 프로그램, AAFC 소개 페이지 구현 + MSSQL 데이터 이관

---

## 1. 모델 설계

### Stadium (lf_stadium)
- MSSQL `lf_stadium` 테이블 매핑 (39건)
- 주요 필드: sta_code(PK), sta_name, sta_phone, sta_address
- 이미지: sta_s_img, sta_l_img (구장 소형/대형 사진)
- 상세: sta_desc(TextField, HTML), location_url(TextField, 구글맵 iframe URL)
- 상태: use_gbn, local_code(권역코드 → CodeValue 연결)

### Coach (lf_coach)
- MSSQL `lf_coach` 테이블 매핑 (139건)
- 주요 필드: coach_code(PK), coach_name, coach_level, dpart
- 이미지: coach_s_img (코치 사진)
- 상세: inve(경력), grou(그룹), three_lecyn
- 상태: use_gbn, sort_num(정렬순서)

### StadiumCoach (lf_stacoach)
- MSSQL `lf_stacoach` 테이블 매핑 (73건)
- 다대다 중간 테이블: stadium(FK→Stadium), coach(FK→Coach)
- unique_together: (stadium, coach)

### Lecture (lf_lecture)
- MSSQL `lf_lecture` 테이블 매핑 (1,180건)
- 주요 필드: lecture_code(PK), lecture_title, stu_cnt(정원), lecture_time
- 분류: class_gbn(클래스구분), class_gbn2, day(요일 1~7)
- FK: stadium(→Stadium), coach(담당코치→Coach), t_coach(수업코치→Coach)
- 메서드: `get_day_display()` → 1=월, 2=화, ..., 7=일 변환
- 상태: use_gbn

### StadiumGoal (lf_stadium_goal)
- MSSQL `lf_stadium_goal` 테이블 매핑 (528건)
- 구장별 목표/일정 정보: stadium(FK), class_gbn, month, week 등

### Promotion (lf_promotion)
- MSSQL `lf_promotion` 테이블 매핑 (1,111건)
- 할인/프로모션 정보: pro_name, pro_code, discount_price, discount_unit
- 모드: use_mode, issue_mode, is_price_limit, is_use (max_length=5, MSSQL 데이터 길이 대응)

---

## 2. 데이터 이관

### 스크립트: `scripts/migrate_courses.py`
- pyodbc로 MSSQL 연결 → Django ORM으로 PostgreSQL에 쓰기
- `update_or_create()` 사용 (멱등성 보장)
- 이관 순서: stadiums → coaches → stadium_coaches → lectures → stadium_goals → promotions

### 헬퍼 함수
- `safe_str(val)`: MSSQL이 int로 반환하는 varchar 필드 대응 → `str(val).strip()`
- `make_aware(dt)`: naive datetime → Asia/Seoul aware 변환
- `combine_phone(a, b, c)`: 전화번호 3분할 → 하이픈 결합
- `checkint(val)`: 문자열/None → int 변환

### LOCATION_MAP
- ASP `loadStadium.asp`의 Select Case에서 추출
- sta_code → 구글맵 iframe src URL 매핑 딕셔너리
- Stadium.location_url 필드에 저장

### 주의사항
- MSSQL varchar 필드가 int로 반환되는 경우 있음 → `safe_str()` 필수
- Promotion의 discount_unit, is_price_limit, is_use 필드: MSSQL 데이터가 1자 초과 → max_length=5

---

## 3. 이미지 파일

### 복사 대상 (2018_fcjunior → aafc/media/)
- `fcdata/coach/` → `media/fcdata/coach/` (964개 코치 사진)
- `fcdata/stadium/` → `media/fcdata/stadium/` (184개 구장 사진)

### 미디어 서빙
- `config/urls.py`에 DEBUG 모드 미디어 서빙 추가
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 4. URL 구조

| URL | 뷰 | 설명 |
|-----|-----|------|
| `/academy/stadium/` | stadium_list_view | 구장안내 (이미지맵 + 모바일 테이블) |
| `/academy/stadium/<sta_code>/` | stadium_detail_view | 구장 상세 (AJAX 파셜) |
| `/academy/coach/` | coach_list_view | 코칭스태프 소개 |
| `/academy/program/` | program_view | 교육 프로그램 |
| `/academy/greeting/` | greeting_view | 운영진 인사말 |
| `/academy/emblem/` | emblem_view | 엠블럼 & BI소개 |
| `/academy/waytocome/` | waytocome_view | 찾아오시는 길 |

---

## 5. Views

### stadium_list_view
- 사용 중인 구장 목록 (use_gbn='Y')
- `_get_local_name_map()` 헬퍼로 CodeValue에서 권역코드→지역명 매핑
- PC: 이미지맵 (junior_stadium_250729.jpg) + area 태그
- 모바일: 테이블 (지역, 구장명, 연락처, 상세보기)

### stadium_detail_view
- AJAX 전용 파셜 템플릿 반환 (base.html 상속 없음)
- 강좌를 class_gbn별 OrderedDict로 그룹핑
- StadiumCoach를 통해 연결된 코치 목록 조회
- 구장 정보 + 강좌 테이블 + 코치 이미지 + 구장사진 + 설명 + 구글맵

### coach_list_view
- 사용 중인 코치 중 이미지가 있는 코치만 표시
- sort_num 순 정렬

### program_view, greeting_view, emblem_view, waytocome_view
- 정적 페이지 (DB 조회 없음)
- 프로그램: 이미지 6장 + YouTube iframe
- 찾아오시는 길: 4개 사무실 (본사, 북부, 고양, 남양주) + 구글맵 iframe

---

## 6. 템플릿 구조

### 구장안내: stadium_list.html
```html
<div id="sub_contents">
    <div class="sub_top academy">...</div>      <!-- 아카데미 상단 배너 -->
    <div class="sub_menu"><ul>...</ul></div>      <!-- 탭 메뉴 -->
    <div class="sub_contents">
        <!-- PC: 이미지맵 -->
        <div class="stadium_map"><img usemap="#stadiumMap" .../>
            <map name="stadiumMap"><area .../>...</map>
        </div>
        <!-- Mobile: 테이블 -->
        <div class="stadium_table"><table>...</table></div>
        <!-- AJAX 로드 영역 -->
        <div id="stadium_detail_area"></div>
    </div>
</div>
```
- `goStadium(sta_code)` JS 함수: `/academy/stadium/<sta_code>/`로 AJAX 호출 → `#stadium_detail_area`에 삽입

### 구장상세: stadium_detail_fragment.html
- base.html 상속 없음 (AJAX 파셜)
- 구장소개 테이블 + 클래스별 강좌 테이블 + 코치 이미지 + 구장사진 + 설명 + 지도

### 코칭스태프: coach_list.html
- `ul.stadium_coach` CSS 클래스 사용
- 코치별 `li > img` 구조

### AAFC 소개: greeting.html, emblem.html, waytocome.html
- sub_top: `aafc` 클래스 (AAFC 배너)
- sub_menu: `submenu_aafc` (운영진 인사말, 엠블럼, 찾아오시는 길)
- 각 페이지에서 해당 메뉴에 `present` 클래스

### 교육 프로그램: program.html
- sub_top: `academy` 클래스 (아카데미 배너)
- sub_menu: `submenu_academy` (구장안내, 코칭스태프, 교육 프로그램)

---

## 7. base.html 네비게이션 업데이트

### PC GNB 메뉴 (header_gnb)
- AAFC 드롭다운: 운영진 인사말, 엠블럼 & BI소개, 찾아오시는 길
- 아카데미 드롭다운: 구장안내, 코칭스태프, 교육 프로그램

### 모바일 메뉴
- AAFC, 아카데미 하위 메뉴 링크 추가

### Quick Menu
- 구장안내 → `courses:stadium_list`

---

## 8. Django Admin

### StadiumAdmin
- list_display: sta_code, sta_name, sta_phone, use_gbn
- list_filter: use_gbn
- search_fields: sta_name, sta_address
- inlines: StadiumCoachInline, LectureInline

### CoachAdmin
- list_display: coach_code, coach_name, coach_level, use_gbn
- list_filter: use_gbn, coach_level
- search_fields: coach_name

### LectureAdmin
- list_display: lecture_code, lecture_title, stadium, day, lecture_time, class_gbn, use_gbn
- list_filter: use_gbn, class_gbn, class_gbn2
- raw_id_fields: stadium, coach, t_coach

### PromotionAdmin
- list_display: pro_code, pro_name, discount_price, discount_unit, is_use
- list_filter: is_use, use_mode, issue_mode

---

## 9. 생성/수정 파일 목록

| 파일 | 작업 |
|------|------|
| `apps/courses/models.py` | Stadium, Coach, StadiumCoach, Lecture, StadiumGoal, Promotion 모델 |
| `apps/courses/views.py` | 7개 뷰 함수 |
| `apps/courses/urls.py` | 신규 - URL 라우팅 (app_name='courses') |
| `apps/courses/admin.py` | 구장/코치/강좌/프로모션 Admin |
| `apps/courses/migrations/0001_initial.py` | 자동 생성 |
| `apps/courses/migrations/0002_alter_promotion_*.py` | Promotion 필드 max_length 수정 |
| `config/urls.py` | academy URL include + 미디어 서빙 추가 |
| `scripts/migrate_courses.py` | 신규 - 6개 테이블 데이터 이관 |
| `templates/base.html` | GNB/모바일/Quick Menu 네비게이션 링크 추가 |
| `templates/courses/stadium_list.html` | 신규 - 구장안내 (이미지맵 + 테이블) |
| `templates/courses/stadium_detail_fragment.html` | 신규 - 구장 상세 (AJAX 파셜) |
| `templates/courses/coach_list.html` | 신규 - 코칭스태프 |
| `templates/courses/program.html` | 신규 - 교육 프로그램 |
| `templates/courses/greeting.html` | 신규 - 운영진 인사말 |
| `templates/courses/emblem.html` | 신규 - 엠블럼 & BI소개 |
| `templates/courses/waytocome.html` | 신규 - 찾아오시는 길 |
| `media/fcdata/coach/` | 코치 이미지 964개 복사 |
| `media/fcdata/stadium/` | 구장 이미지 184개 복사 |
