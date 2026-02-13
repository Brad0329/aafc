# Phase 2 테스트 가이드: 강좌 + 구장 + 코치

## 사전 준비
```bash
cd c:\Users\user\Documents\aafc
python manage.py runserver
```
브라우저에서 `http://127.0.0.1:8000` 접속

---

## 1. 데이터 이관 검증

### 1-1. 데이터 건수 확인
```bash
python manage.py shell -c "from apps.courses.models import Stadium, Coach, StadiumCoach, Lecture, StadiumGoal, Promotion; print(f'Stadium: {Stadium.objects.count()}건, Coach: {Coach.objects.count()}건, StadiumCoach: {StadiumCoach.objects.count()}건, Lecture: {Lecture.objects.count()}건, StadiumGoal: {StadiumGoal.objects.count()}건, Promotion: {Promotion.objects.count()}건')"
```
- [ ] Stadium: 39건
- [ ] Coach: 139건
- [ ] StadiumCoach: 73건
- [ ] Lecture: 1,180건
- [ ] StadiumGoal: 528건
- [ ] Promotion: 1,111건

### 1-2. 샘플 구장 데이터 확인
```bash
python manage.py shell -c "from apps.courses.models import Stadium; s = Stadium.objects.filter(use_gbn='Y').first(); print(f'구장명: {s.sta_name}, 연락처: {s.sta_phone}, 주소: {s.sta_address}, sta_code: {s.sta_code}')"
```
- [ ] 구장명, 연락처, 주소가 정상적으로 출력되는지

### 1-3. 샘플 코치 데이터 확인
```bash
python manage.py shell -c "from apps.courses.models import Coach; c = Coach.objects.filter(use_gbn='Y').first(); print(f'코치명: {c.coach_name}, 레벨: {c.coach_level}, 이미지: {c.coach_s_img}')"
```
- [ ] 코치명, 레벨, 이미지 파일명이 정상적으로 출력되는지

### 1-4. 구장-코치 연결 확인
```bash
python manage.py shell -c "from apps.courses.models import StadiumCoach; sc = StadiumCoach.objects.select_related('stadium','coach').first(); print(f'구장: {sc.stadium.sta_name} ↔ 코치: {sc.coach.coach_name}')"
```
- [ ] 구장과 코치가 정상 연결되어 있는지

### 1-5. 강좌 데이터 확인
```bash
python manage.py shell -c "from apps.courses.models import Lecture; l = Lecture.objects.filter(use_gbn='Y').select_related('stadium').first(); print(f'강좌: {l.lecture_title}, 구장: {l.stadium.sta_name}, 요일: {l.get_day_display()}, 시간: {l.lecture_time}, 정원: {l.stu_cnt}')"
```
- [ ] 강좌명, 구장명, 요일(한글), 시간, 정원이 정상 출력되는지

---

## 2. 구장안내 페이지 테스트

### 2-1. 구장안내 목록 (PC)
- [ ] `http://127.0.0.1:8000/academy/stadium/` 접속
- [ ] 구장 이미지맵 (junior_stadium_250729.jpg) 표시되는지 확인
- [ ] 이미지맵의 구장명 위에 마우스 올리면 커서가 바뀌는지 확인

### 2-2. 구장안내 목록 (모바일)
- [ ] 브라우저 폭을 줄여서 모바일 뷰로 전환
- [ ] 테이블 형태 (지역, 구장명, 연락처, 상세보기) 표시되는지 확인
- [ ] 전체 구장이 리스트에 표시되는지 확인

### 2-3. 구장 상세 (AJAX 로드)
- [ ] PC: 이미지맵에서 구장 클릭
- [ ] 모바일: 테이블의 "상세보기" 버튼 클릭
- [ ] 하단에 구장상세 정보가 AJAX로 로드되는지 확인
- [ ] 구장소개 테이블 (구장명, 연락처, 주소) 표시
- [ ] 강좌 정보 (클래스별 요일, 시간, 대상, 정원) 표시
- [ ] 담당코치 이미지 표시
- [ ] 구장사진 (sta_s_img, sta_l_img) 표시
- [ ] 소개 (sta_desc HTML) 표시 (있는 경우)
- [ ] 구장위치 구글맵 iframe 표시 (있는 경우)

### 2-4. 다른 구장 클릭 시 갱신
- [ ] 구장 A 클릭 후 구장 B 클릭
- [ ] 상세 정보가 구장 B로 변경되는지 확인

---

## 3. 코칭스태프 페이지 테스트

### 3-1. 코칭스태프 목록
- [ ] `http://127.0.0.1:8000/academy/coach/` 접속
- [ ] 코치 이미지들이 격자 형태로 표시되는지 확인
- [ ] 이미지 경로가 `/media/fcdata/coach/파일명`으로 정상 로드되는지 확인

### 3-2. 이미지 없는 경우
- [ ] coach_s_img가 없는 코치는 표시되지 않는지 확인

---

## 4. 교육 프로그램 페이지 테스트

### 4-1. 페이지 표시
- [ ] `http://127.0.0.1:8000/academy/program/` 접속
- [ ] 프로그램 이미지 6장 (program_img_01~06.jpg) 표시되는지 확인
- [ ] YouTube 동영상 iframe 표시 및 재생 가능한지 확인

---

## 5. AAFC 소개 페이지 테스트

### 5-1. 운영진 인사말
- [ ] `http://127.0.0.1:8000/academy/greeting/` 접속
- [ ] 인사말 이미지 (aafc_greeting.jpg) 표시되는지 확인
- [ ] 서브메뉴에서 "운영진 인사말"이 활성(present) 상태인지 확인

### 5-2. 엠블럼 & BI소개
- [ ] `http://127.0.0.1:8000/academy/emblem/` 접속
- [ ] 엠블럼 이미지 표시되는지 확인
- [ ] 서브메뉴에서 "엠블럼 & BI소개"가 활성 상태인지 확인

### 5-3. 찾아오시는 길
- [ ] `http://127.0.0.1:8000/academy/waytocome/` 접속
- [ ] 4개 사무실 정보 표시 (본사, 북부, 고양, 남양주)
- [ ] 각 사무실의 구글맵 iframe 로드되는지 확인
- [ ] 서브메뉴에서 "찾아오시는 길"이 활성 상태인지 확인

---

## 6. 네비게이션 링크 테스트

### 6-1. PC GNB 메뉴
- [ ] AAFC 메뉴 hover → 드롭다운 (운영진 인사말, 엠블럼 & BI소개, 찾아오시는 길)
- [ ] 아카데미 메뉴 hover → 드롭다운 (구장안내, 코칭스태프, 교육 프로그램)
- [ ] 각 링크 클릭 시 해당 페이지로 이동하는지 확인

### 6-2. 모바일 메뉴
- [ ] 햄버거 메뉴 열기
- [ ] AAFC 하위메뉴 (운영진 인사말, 엠블럼 & BI소개, 찾아오시는 길) 링크 동작
- [ ] 아카데미 하위메뉴 (구장안내, 코칭스태프, 교육 프로그램) 링크 동작

### 6-3. Quick Menu
- [ ] 우측 QUICK MENU의 "구장안내" 클릭 → 구장안내 페이지 이동

---

## 7. 서브메뉴 활성 표시 테스트

### 7-1. 아카데미 섹션
- [ ] 구장안내 페이지: "구장안내" 메뉴에 `present` 클래스
- [ ] 코칭스태프 페이지: "코칭스태프" 메뉴에 `present` 클래스
- [ ] 교육 프로그램 페이지: "교육 프로그램" 메뉴에 `present` 클래스

### 7-2. AAFC 섹션
- [ ] 운영진 인사말: "운영진 인사말" 메뉴에 `present` 클래스
- [ ] 엠블럼 & BI소개: "엠블럼 & BI소개" 메뉴에 `present` 클래스
- [ ] 찾아오시는 길: "찾아오시는 길" 메뉴에 `present` 클래스

---

## 8. 이미지 서빙 테스트

### 8-1. 코치 이미지
- [ ] `http://127.0.0.1:8000/media/fcdata/coach/` 경로의 이미지가 로드되는지 확인
- [ ] 코칭스태프 페이지에서 이미지 깨짐 없는지 확인

### 8-2. 구장 이미지
- [ ] 구장 상세에서 구장사진 (sta_s_img, sta_l_img) 이미지 로드 확인
- [ ] 이미지 경로: `/media/fcdata/stadium/파일명`

---

## 9. Django Admin 테스트

### 9-1. 관리자 접속
- [ ] `http://127.0.0.1:8000/admin/` 접속 (admin / admin1234)

### 9-2. 구장 관리
- [ ] Courses > Stadiums 목록 표시 (sta_code, 구장명, 연락처, 사용여부)
- [ ] 사용여부(use_gbn) 필터 동작
- [ ] 검색 (구장명, 주소)으로 구장 찾기
- [ ] 구장 상세 페이지에서 인라인 코치 목록 표시

### 9-3. 코치 관리
- [ ] Courses > Coaches 목록 표시 (coach_code, 코치명, 레벨, 사용여부)
- [ ] 사용여부, 레벨 필터 동작
- [ ] 검색 (코치명)으로 코치 찾기

### 9-4. 강좌 관리
- [ ] Courses > Lectures 목록 표시 (lecture_code, 강좌명, 구장, 요일, 시간, 클래스, 사용여부)
- [ ] 사용여부, 클래스(class_gbn, class_gbn2) 필터 동작
- [ ] 구장, 코치 FK 필드가 raw_id_fields로 표시

### 9-5. 프로모션 관리
- [ ] Courses > Promotions 목록 표시
- [ ] 사용여부, 사용모드, 발급모드 필터 동작

---

## 10. 디자인 확인

### 10-1. 기존 ASP 사이트와 비교
- [ ] 구장안내: 이미지맵 레이아웃이 기존과 동일한지
- [ ] 구장 상세: 테이블 스타일, 코치 이미지 배치가 기존과 동일한지
- [ ] 코칭스태프: 이미지 격자 레이아웃이 기존과 동일한지
- [ ] 교육 프로그램: 이미지 + YouTube 배치가 기존과 동일한지
- [ ] AAFC 소개: sub_top 배너, 서브메뉴 스타일이 기존과 동일한지

### 10-2. 모바일 반응형
- [ ] 구장안내: PC 이미지맵 숨김, 모바일 테이블 표시
- [ ] 각 페이지에서 모바일 레이아웃 깨짐 없는지

---

## 테스트 결과 요약

| 항목 | 결과 |
|------|------|
| 데이터 이관 | |
| 구장안내 (목록) | |
| 구장안내 (상세 AJAX) | |
| 코칭스태프 | |
| 교육 프로그램 | |
| 운영진 인사말 | |
| 엠블럼 & BI소개 | |
| 찾아오시는 길 | |
| 네비게이션 링크 | |
| 서브메뉴 활성 표시 | |
| 이미지 서빙 | |
| Django Admin | |
| 디자인 (PC/모바일) | |

테스트 일자:
테스트자:
