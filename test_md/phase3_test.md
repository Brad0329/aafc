# Phase 3 테스트 가이드: 수강신청 + 결제

## 사전 준비
```bash
cd c:\Users\user\Documents\aafc
python manage.py runserver
```
브라우저에서 `http://127.0.0.1:8080` 접속

**필수 조건**: 로그인 + 자녀 1명 이상 등록 상태

---

## 1. 데이터 이관 검증

### 1-1. 건수 확인
```bash
python manage.py shell -c "
from apps.courses.models import LectureSelDay, PromotionMember
from apps.enrollment.models import Enrollment, EnrollmentCourse, EnrollmentBill, WaitStudent
from apps.payments.models import PaymentKCP, PaymentFail
print(f'LectureSelDay: {LectureSelDay.objects.count()}건')
print(f'Enrollment: {Enrollment.objects.count()}건')
print(f'EnrollmentBill: {EnrollmentBill.objects.count()}건')
print(f'EnrollmentCourse: {EnrollmentCourse.objects.count()}건')
print(f'WaitStudent: {WaitStudent.objects.count()}건')
print(f'PaymentKCP: {PaymentKCP.objects.count()}건')
print(f'PaymentFail: {PaymentFail.objects.count()}건')
"
```
- [ ] LectureSelDay: 196,609건
- [ ] Enrollment: 79,490건
- [ ] EnrollmentBill: 131,280건
- [ ] EnrollmentCourse: 220,596건
- [ ] WaitStudent: 107건
- [ ] PaymentKCP: 42,721건
- [ ] PaymentFail: 1,138건

### 1-2. 샘플 데이터 확인
```bash
python manage.py shell -c "
from apps.enrollment.models import Enrollment
e = Enrollment.objects.filter(pay_stats='PY').first()
print(f'#{e.id} 회원:{e.member_id} 자녀:{e.child_id} 결제:{e.pay_price}원 수강:{e.get_lecture_stats_display()} 기간:{e.start_dt}~{e.end_dt}')
"
```
- [ ] 결제완료 건이 정상적으로 조회되는지

---

## 2. 네비게이션 확인

### 2-1. PC 헤더 GNB
- [ ] `http://127.0.0.1:8080/` 접속
- [ ] "입단신청" 메뉴 클릭 → `/enrollment/apply/` 이동
- [ ] "마이아카데미" 마우스 오버 → 드롭다운 (마이페이지, 결제내역, 비밀번호 변경)
- [ ] "결제내역" 클릭 → `/enrollment/payment-history/` 이동

### 2-2. 모바일 메뉴
- [ ] 브라우저 폭 줄여서 모바일 모드
- [ ] 햄버거 메뉴에서 "입단신청" 링크 정상
- [ ] "마이아카데미" 하위에 결제내역 표시

### 2-3. QUICK MENU
- [ ] 우측 사이드바 "입단신청" 아이콘 클릭 → `/enrollment/apply/` 이동

### 2-4. 서브메뉴 (마이아카데미 하위)
- [ ] 마이페이지 → 서브메뉴에 "마이페이지 | 결제내역 | 비밀번호 변경" 3개
- [ ] 결제내역 → 서브메뉴에 "마이페이지 | 결제내역 | 비밀번호 변경" 3개
- [ ] 비밀번호 변경 → 서브메뉴에 "마이페이지 | 결제내역 | 비밀번호 변경" 3개

---

## 3. 수강신청 Step 1 (자녀선택 → 강좌선택)

### 3-1. 페이지 접근
- [ ] `http://127.0.0.1:8080/enrollment/apply/` 접속
- [ ] 페이지 디자인: sub_top 이미지, sub_menu, sub_tit 정상 표시
- [ ] 자녀 목록이 표시되는지 (라디오 버튼)

### 3-2. 비로그인 접근
- [ ] 로그아웃 → `/enrollment/apply/` 직접 입력
- [ ] 로그인 페이지로 리다이렉트 되는지

### 3-3. 자녀 선택
- [ ] 자녀 라디오 버튼 클릭 시 선택되는지
- [ ] 이미 수강 중인 자녀가 있으면 "수강중" 표시 + 선택 불가

### 3-4. 권역 → 구장 AJAX
- [ ] 권역 라디오 버튼 클릭
- [ ] 해당 권역의 구장 목록이 아래에 로드되는지 (AJAX)
- [ ] 제외 구장 (sta_code: 4, 17, 20, 35) 이 표시되지 않는지

### 3-5. 구장 → 강좌 AJAX
- [ ] 구장 라디오 버튼 클릭
- [ ] 해당 구장의 강좌 목록이 테이블로 로드되는지 (AJAX)
- [ ] 각 강좌에 요일, 시간, 대상, 정원, 현재원, 상태(가능/대기/마감) 표시

### 3-6. 강좌 선택 → 시작일 AJAX
- [ ] 강좌 체크박스 선택 (주간횟수에 맞게)
- [ ] 선택한 강좌별 수업 시작일 라디오 버튼 목록 로드 (AJAX)

### 3-7. 대기 등록
- [ ] 정원이 찬 강좌(상태=대기)를 선택 시 대기 등록 버튼 표시
- [ ] 대기 등록 클릭 → "대기 N번으로 등록되었습니다" 메시지
- [ ] 동일 강좌 중복 대기 등록 시 "이미 대기 등록하신 강좌입니다" 메시지

### 3-8. 추천인 확인
- [ ] 추천인 아이디 입력 → "확인" 클릭
- [ ] 존재하는 아이디: "확인되었습니다"
- [ ] 존재하지 않는 아이디: "존재하지 않는 아이디입니다"
- [ ] 자신의 아이디: "유효하지 않은 아이디입니다"

### 3-9. 다음 단계 이동
- [ ] 자녀, 구장, 강좌, 시작일 모두 선택 후 "다음" 클릭
- [ ] Step 2 페이지로 이동

---

## 4. 수강신청 Step 2 (프로모션/할인 확인)

### 4-1. 선택 요약 표시
- [ ] 권역명, 구장명, 선택 강좌 목록 정상 표시
- [ ] 강좌별 수업일, 시간, 수업횟수, 수강료 계산 표시
- [ ] 교육용품비 표시 (재등록 시 0원)

### 4-2. 프로모션/할인 AJAX
- [ ] 페이지 로드 시 할인 테이블이 AJAX로 로드되는지
- [ ] 6종 할인 항목 표시: 교육용품비, 수강료, 결제금액, 3개월선납, 피추천, 다회할인
- [ ] 해당 없는 항목은 "해당내역이 없습니다" 표시

### 4-3. 다회할인 (주2회 이상)
- [ ] 주2회 수업 선택 시 dc_2 기반 할인 금액 계산
- [ ] 주3회 이상 선택 시 dc_3 기반 할인 금액 계산

### 4-4. 다음 단계 이동
- [ ] "다음" 클릭 → Step 3 페이지로 이동

---

## 5. 수강신청 Step 3 (결제 확인)

### 5-1. 결제 정보 요약
- [ ] 구장명, 자녀명, 신청자명 표시
- [ ] 교육용품비, 수강료, 할인 내역 표시
- [ ] 총 결제금액 = 교육용품비 + 수강료 - 할인 합계

### 5-2. 결제수단 선택
- [ ] 신용카드 / 계좌이체 라디오 버튼
- [ ] 선택 변경 시 hidden 필드 (use_pay_method) 값 변경되는지

### 5-3. 결제하기 (테스트 모드)
- [ ] "결제하기" 클릭 → 확인 팝업 (결제금액 표시)
- [ ] "확인" 클릭 → 결제 성공 페이지 이동 (테스트 모드이므로 바로 성공)
- [ ] "취소" 클릭 → 결제 진행 안됨

### 5-4. 이전 단계
- [ ] "이전단계" 클릭 → 뒤로 이동

---

## 6. 결제 성공 페이지

### 6-1. 결제 완료 표시
- [ ] "입단신청이 완료되었습니다!" 메시지
- [ ] 신청번호, 결제금액, 수강기간, 수강상태 표시

### 6-2. 링크 동작
- [ ] "결제내역 확인" 클릭 → 결제내역 페이지
- [ ] "홈으로" 클릭 → 메인 페이지

---

## 7. 결제 실패 페이지

### 7-1. 실패 표시 (세션 만료 시뮬레이션)
- [ ] 세션 없이 `/payments/kcp/return/` POST 시도
- [ ] "세션이 만료되었습니다" 메시지 표시

### 7-2. 링크 동작
- [ ] "다시 시도" 클릭 → Step 1 페이지
- [ ] "홈으로" 클릭 → 메인 페이지

---

## 8. 결제내역 페이지

### 8-1. 목록 표시
- [ ] `http://127.0.0.1:8080/enrollment/payment-history/` 접속
- [ ] 테이블 컬럼: 번호, 자녀, 결제방법, 결제금액, 시작월, 종료월, 결제상태, 수강상태
- [ ] 결제상태: "결제완료" (파란색) / "미결제" (빨간색)

### 8-2. 방금 결제한 건 확인
- [ ] Step 1~3 으로 결제 완료한 건이 목록 최상단에 표시

### 8-3. 페이지네이션
- [ ] 10건 이상일 때 페이지 번호 표시
- [ ] 이전/다음 링크 동작

### 8-4. 비로그인 접근
- [ ] 로그아웃 → `/enrollment/payment-history/` 직접 입력
- [ ] 로그인 페이지로 리다이렉트

---

## 9. Django Admin 확인

### 9-1. 입단신청 관리
- [ ] `http://127.0.0.1:8080/admin/enrollment/enrollment/` 접속
- [ ] 목록: 번호, 회원, 자녀, 결제상태, 결제금액, 수강상태, 등록일
- [ ] 검색 (회원ID, 자녀ID)
- [ ] 필터 (결제상태, 수강상태, 신청구분)

### 9-2. 입단 상세 (인라인)
- [ ] 입단 상세 페이지 → 청구내역(EnrollmentBill) 인라인 표시
- [ ] 입단 상세 페이지 → 수강과정(EnrollmentCourse) 인라인 표시

### 9-3. 대기자 관리
- [ ] `http://127.0.0.1:8080/admin/enrollment/waitstudent/` 접속
- [ ] 목록 표시 + 검색/필터 동작

### 9-4. KCP 결제 로그
- [ ] `http://127.0.0.1:8080/admin/payments/paymentkcp/` 접속
- [ ] 주문번호, 금액, 응답코드, 구매자, 등록일 표시
- [ ] 검색 (주문번호, 구매자) 동작

### 9-5. 결제 실패 로그
- [ ] `http://127.0.0.1:8080/admin/payments/paymentfail/` 접속
- [ ] 실패 기록 목록 표시

### 9-6. 수업일 스케줄
- [ ] `http://127.0.0.1:8080/admin/courses/lectureselday/` 접속
- [ ] 강좌별 년/월/일 스케줄 데이터 표시

---

## 10. 비즈니스 룰 테스트

### 10-1. 중복 수강 방지
- [ ] 이미 수강확정(LY) 상태인 자녀로 Step 1 진입
- [ ] "수강중" 표시 + 해당 자녀 선택 불가

### 10-2. 21일 규칙
- [ ] 오늘이 21일 이전이면 당월 시작 표시
- [ ] 오늘이 22일 이후이면 익월 시작 표시
```bash
python manage.py shell -c "
from apps.enrollment.views import _get_start_month
year, month = _get_start_month()
print(f'시작년월: {year}년 {month}월')
"
```

### 10-3. 교육용품비 면제
- [ ] 재등록 자녀(course_state: PAU/END/CAN) → 교육용품비 0원
- [ ] 신규 자녀 → 교육용품비 표시 (Setting.join_price)

### 10-4. 은평롯데몰 (sta_code=11) 제외 확인
- [ ] sta_code=11이 구장 목록에서 제외 구장 리스트에 포함되지는 않지만, 결제 불가 처리가 되는지 확인 (비즈니스 로직 확인)

---

## 11. 전체 플로우 E2E 테스트

### 11-1. 신규 수강신청 전체 과정
1. [ ] 로그인
2. [ ] 입단신청 클릭
3. [ ] 자녀 선택
4. [ ] 권역 선택 → 구장 로드
5. [ ] 구장 선택 → 강좌 로드
6. [ ] 강좌 선택 → 시작일 로드
7. [ ] 시작일 선택 → "다음" 클릭
8. [ ] Step 2: 요약 확인 + 프로모션 로드 → "다음" 클릭
9. [ ] Step 3: 결제 정보 확인 → "결제하기" 클릭
10. [ ] 결제 성공 페이지 표시
11. [ ] "결제내역 확인" → 결제내역에 방금 건 표시
12. [ ] Admin에서 Enrollment + EnrollmentBill + EnrollmentCourse 생성 확인
13. [ ] Admin에서 PaymentKCP 로그 생성 확인
14. [ ] 자녀 수강상태가 'ING'으로 변경되었는지 Admin 확인

---

## 테스트 결과 요약

| 항목 | 결과 |
|------|------|
| 데이터 이관 | |
| 네비게이션 | |
| Step 1 (자녀/구장/강좌 선택) | |
| Step 1 AJAX (구장/강좌/시작일) | |
| Step 1 대기등록/추천인 | |
| Step 2 (프로모션/할인) | |
| Step 3 (결제 확인) | |
| 결제 성공 | |
| 결제 실패 | |
| 결제내역 | |
| Django Admin | |
| 비즈니스 룰 (중복/21일/면제) | |
| E2E 전체 플로우 | |

테스트 일자:
테스트자:
