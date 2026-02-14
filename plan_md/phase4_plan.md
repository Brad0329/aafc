# Phase 4 구현 계획: 게시판 + 상담

## 목표
커뮤니티 기능 (게시판 9종 + 상담신청 + 무료체험신청) 구현 + MSSQL 데이터 이관

---

## 1. 모델 설계

### Board (lf_board)
- MSSQL `lf_board` 테이블 매핑 (355건)
- 주요 필드: b_seq(게시글번호, unique), b_gbn(게시판구분), b_title, b_content(TextField)
- 구분: b_gbn → Y(공지), N(소식), E(이벤트), P(포토), PR(학부모다이어리), ST(공부하는AAFC), U8/U10/U12(클래식반)
- 공지: b_notice_yn='Y'인 게시글은 목록 상단 고정
- 작성자: b_writer, b_writer_id
- 날짜: insert_dt(CharField, max_length=20) - MSSQL 원본 그대로 유지
- 조회수: b_hit(IntegerField)
- 상태: del_chk='N'(정상), 'Y'(삭제)

### BoardComment (lf_boardcomment)
- MSSQL `lf_boardcomment` 테이블 매핑 (44건)
- FK → Board (to_field='b_seq', related_name='comments')
- 주요 필드: comment_content(TextField), comment_writer, comment_writer_id
- 날짜: insert_dt(CharField)
- 상태: del_chk

### BoardFile (lf_boardsub)
- MSSQL `lf_boardsub` 테이블 매핑 (65건)
- FK → Board (to_field='b_seq', related_name='files')
- 주요 필드: file_name(원본파일명), file_path(저장경로), file_size

### Consult (lf_consult)
- MSSQL `lf_consult` 테이블 매핑 (2,746건)
- 주요 필드: consult_name(신청자명), consult_tel, consult_content
- 구장: sta_code(CharField) - Stadium 모델 직접 참조하지 않음
- 분류: consult_gbn(상담유형), real_gbn(실제구분)
- 개인정보: child_name, child_birth, child_school
- 날짜: insert_dt(CharField)
- 상태: del_chk

### ConsultAnswer (lf_con_answer)
- MSSQL `lf_con_answer` 테이블 매핑 (2,743건, 7건 orphan skip)
- FK → Consult (related_name='answers')
- 주요 필드: answer_content(TextField), stat_code(IntegerField)
- 상담상태: stat_code → 76(접수), 77(완료), 78(이관)
- 날짜: insert_dt(CharField)

### ConsultFree (lf_consult_free)
- MSSQL `lf_consult_free` 테이블 매핑 (396건)
- 무료수업체험 신청
- 주요 필드: free_name, free_tel, free_local(지역)
- 날짜: insert_dt(CharField)
- 상태: del_chk

### ConsultRegion (lf_consult_uplocal)
- MSSQL `lf_consult_uplocal` 테이블 매핑 (54건)
- 상담 지역 관리 (시/군/구 단위)
- 주요 필드: local_name(지역명), sta_code(구장코드)
- 정렬: sort_num

---

## 2. 데이터 이관

### 스크립트: `scripts/migrate_board.py`
- pyodbc로 MSSQL 연결 → Django ORM으로 PostgreSQL에 쓰기
- 이관 순서: Board → BoardComment → BoardFile
- `update_or_create()` 사용 (멱등성 보장)
- BoardComment/BoardFile: board FK를 b_seq(to_field)로 연결

### 스크립트: `scripts/migrate_consult.py`
- 이관 순서: ConsultRegion → ConsultFree → Consult → ConsultAnswer
- ConsultAnswer: consult FK 매핑 시 seq_id_map 딕셔너리 사용
- orphan 레코드(부모 Consult 없는 Answer) skip 처리

### 헬퍼 함수
- `safe_str(val)`: MSSQL int 반환 대응
- `make_aware(dt)`: naive datetime → Asia/Seoul aware 변환
- `checkint(val)`: 문자열/None → int 변환

---

## 3. URL 구조

### Board URLs (app_name='board')

| URL | 뷰 | 설명 |
|-----|-----|------|
| `/board/<b_gbn>/` | board_list | 게시판 목록 |
| `/board/<b_gbn>/write/` | board_write | 글쓰기 |
| `/board/<b_gbn>/<board_id>/` | board_view | 글 상세 |
| `/board/<b_gbn>/<board_id>/edit/` | board_edit | 글 수정 |
| `/board/<b_gbn>/<board_id>/delete/` | board_delete | 글 삭제 |
| `/board/comment/add/` | comment_add | 댓글 등록 |
| `/board/comment/<comment_id>/delete/` | comment_delete | 댓글 삭제 |

- comment 라우트를 board_id 라우트보다 먼저 배치 (URL 충돌 방지)

### Consult URLs (app_name='consult')

| URL | 뷰 | 설명 |
|-----|-----|------|
| `/consult/` | consult_form | 상담신청 |
| `/consult/free/` | consult_free_form | 무료수업체험 신청 |
| `/consult/done/` | consult_done (template) | 신청완료 |
| `/consult/api/search-stadium/` | ajax_search_stadium | AJAX 구장검색 |

---

## 4. Views

### Board Views

#### board_list
- BOARD_CONFIG 딕셔너리로 게시판 타입별 설정 관리 (타이틀, 메뉴, CSS 클래스 등)
- COMMUNITY_MENU 리스트로 좌측 사이드 메뉴 생성
- 공지글(b_notice_yn='Y') 상단 고정 + 일반글 페이지네이션 (15건/페이지)
- 검색 지원: 제목(title), 내용(content), 제목+내용(both), 작성자(writer)
- 포토갤러리(P): 그리드 레이아웃 (notice_photo CSS)
- U8/U10/U12 접근 시 클래식반 페이지로 리다이렉트

#### board_view
- 조회수 증가 (b_hit += 1)
- 댓글 목록 (del_chk='N')
- 첨부파일 목록
- 이전글/다음글 네비게이션 (같은 게시판, 삭제 안 된 글)

#### board_write
- 로그인 필수 (@login_required)
- CKEditor 5 연동 (CDN, ES module importmap)
- b_seq 자동 생성: Board.objects.aggregate(Max('b_seq')) + 1
- b_ref 자동 생성: 같은 게시판 내 max b_ref + 1

#### board_edit
- 작성자 본인 확인 (b_writer_id == request.user.username)
- CKEditor 5 에디터에 기존 내용 로드

#### board_delete
- 소프트 삭제 (del_chk='Y')
- 작성자 본인 확인

#### comment_add
- POST 전용
- 로그인 필수
- 댓글 작성 후 board_view로 redirect

#### comment_delete
- 소프트 삭제 (del_chk='Y')
- 작성자 본인 확인

### Consult Views

#### consult_form
- 개인정보 동의 → 지역검색 → 구장선택 → 폼입력
- 상담유형: CodeValue.objects.filter(group__grpcode='CONT', del_chk='N').order_by('code_order')
- POST 처리: Consult 생성 + ConsultAnswer(stat_code=76, 접수) 자동 생성
- 완료 후 consult_done 페이지로 redirect

#### consult_free_form
- 개인정보 동의 → 이름/연락처/지역 입력
- POST 처리: ConsultFree 생성
- 완료 후 consult_done 페이지로 redirect

#### ajax_search_stadium
- GET 파라미터: keyword (지역명)
- ConsultRegion에서 지역명 검색 → 매칭되는 구장 목록 반환
- 파셜 템플릿(stadium_search_result.html) 렌더링하여 HTML 반환

---

## 5. 템플릿 구조

### 게시판 목록: board_list.html
```html
<div id="sub_contents">
    <div class="sub_top community">...</div>    <!-- 커뮤니티 상단 배너 -->
    <div class="sub_menu"><ul>...</ul></div>      <!-- 좌측 메뉴 -->
    <div class="sub_contents">
        <!-- 포토갤러리(P): notice_photo 그리드 -->
        <!-- 일반 게시판: notice_normal 테이블 -->
        <!-- 공지사항 상단 고정 + 일반글 + 페이지네이션 -->
        <!-- 검색 폼 -->
    </div>
</div>
```

### 게시판 상세: board_view.html
- 클래식반(U8/U10/U12): 탭 메뉴 (U8/U10/U12 전환)
- 일반 게시판: 제목/작성자/날짜/조회수 + 본문 + 첨부파일 + 댓글
- 이전글/다음글 네비게이션
- 수정/삭제 버튼 (작성자 본인만)

### 글쓰기: board_write.html
- CKEditor 5 CDN via ES module importmap
```html
<script type="importmap">
{ "imports": { "ckeditor5": "https://cdn.ckeditor.com/ckeditor5/41.4.2/ckeditor5.js", ... }}
</script>
<script type="module">
import { ClassicEditor, ... } from 'ckeditor5';
ClassicEditor.create(document.querySelector('#id_b_content'), { ... });
</script>
```

### 글수정: board_edit.html
- board_write.html과 동일한 CKEditor 설정
- 기존 데이터 pre-load

### 상담신청: consult.html
- 개인정보 동의 체크박스
- 지역 검색 입력 → AJAX 구장검색 → 라디오 버튼 선택
- 상담유형 셀렉트 (CodeValue)
- 신청자 정보 (이름, 연락처, 자녀명, 생년월일 등)

### 무료체험: cfree.html
- 개인정보 동의 체크박스
- 이름, 연락처, 지역 입력

### 신청완료: consult_done.html
- 간단한 완료 메시지

### AJAX 파셜: fragments/stadium_search_result.html
- 검색 결과 구장 목록 (라디오 버튼)

---

## 6. CKEditor 5 연동

### 설치
- `pip install django-ckeditor-5`
- INSTALLED_APPS에 `django_ckeditor_5` 추가
- CDN 방식(v41.4.2) 사용 - 서버에 에디터 파일 없음

### config/settings/base.py 설정
```python
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', ...],
    }
}
```

### config/urls.py
```python
path("ckeditor5/", include('django_ckeditor_5.urls')),
```

---

## 7. base.html 네비게이션 업데이트

### PC GNB 메뉴 (header_gnb)
- 커뮤니티 드롭다운: 공지사항, AAFC 소식, 이벤트, 포토갤러리, 학부모 다이어리, 공부하는 AAFC, 클래식반
- 상담 드롭다운: 상담신청, 무료수업체험

### 모바일 메뉴
- 커뮤니티, 상담 하위 메뉴 링크 추가

### Quick Menu
- 커뮤니티/상담 관련 링크 추가

---

## 8. Django Admin

### BoardAdmin
- list_display: b_seq, b_gbn, b_title, b_writer, insert_dt, b_hit, del_chk
- list_filter: b_gbn, del_chk, b_notice_yn
- search_fields: b_title, b_content, b_writer
- inlines: BoardFileInline, BoardCommentInline

### ConsultAdmin
- list_display: id, consult_name, consult_tel, sta_code, consult_gbn, insert_dt, del_chk
- list_filter: consult_gbn, del_chk
- search_fields: consult_name, consult_tel
- inlines: ConsultAnswerInline

### ConsultFreeAdmin
- list_display: id, free_name, free_tel, free_local, insert_dt, del_chk
- list_filter: del_chk
- search_fields: free_name, free_tel

### ConsultRegionAdmin
- list_display: id, local_name, sta_code, sort_num
- search_fields: local_name

---

## 9. 생성/수정 파일 목록

| 파일 | 작업 |
|------|------|
| `apps/board/models.py` | Board, BoardComment, BoardFile 모델 |
| `apps/board/views.py` | 7개 뷰 함수 (list/view/write/edit/delete/comment_add/comment_delete) |
| `apps/board/urls.py` | 신규 - URL 라우팅 (app_name='board') |
| `apps/board/admin.py` | BoardAdmin + inlines |
| `apps/board/migrations/0001_initial.py` | 자동 생성 |
| `apps/consult/models.py` | Consult, ConsultAnswer, ConsultFree, ConsultRegion 모델 |
| `apps/consult/views.py` | 3개 뷰 함수 (consult_form/consult_free_form/ajax_search_stadium) |
| `apps/consult/urls.py` | 신규 - URL 라우팅 (app_name='consult') |
| `apps/consult/admin.py` | ConsultAdmin, ConsultFreeAdmin, ConsultRegionAdmin + inlines |
| `apps/consult/migrations/0001_initial.py` | 자동 생성 |
| `config/settings/base.py` | django_ckeditor_5 추가, CKEditor 5 설정 |
| `config/urls.py` | board, consult, ckeditor5 URL include 추가 |
| `scripts/migrate_board.py` | 신규 - Board/Comment/File 데이터 이관 |
| `scripts/migrate_consult.py` | 신규 - Consult/Answer/Free/Region 데이터 이관 |
| `templates/base.html` | GNB/모바일/Quick Menu 네비게이션 링크 추가 |
| `templates/board/board_list.html` | 신규 - 게시판 목록 |
| `templates/board/board_view.html` | 신규 - 게시판 상세 |
| `templates/board/board_write.html` | 신규 - 글쓰기 (CKEditor 5) |
| `templates/board/board_edit.html` | 신규 - 글수정 (CKEditor 5) |
| `templates/consult/consult.html` | 신규 - 상담신청 |
| `templates/consult/cfree.html` | 신규 - 무료수업체험 |
| `templates/consult/consult_done.html` | 신규 - 신청완료 |
| `templates/consult/fragments/stadium_search_result.html` | 신규 - AJAX 구장검색 결과 |
| `test_md/phase4_test.md` | 신규 - Phase 4 테스트 가이드 |

---

## 10. 데이터 이관 결과

| 모델 | MSSQL 원본 | PostgreSQL 이관 | 비고 |
|------|-----------|----------------|------|
| Board | 355 | 355 | 전체 이관 |
| BoardComment | 44 | 44 | 전체 이관 |
| BoardFile | 65 | 65 | 전체 이관 |
| ConsultRegion | 54 | 54 | 전체 이관 |
| ConsultFree | 396 | 396 | 전체 이관 |
| Consult | 2,746 | 2,746 | 전체 이관 |
| ConsultAnswer | 2,750 | 2,743 | 7건 orphan skip |
