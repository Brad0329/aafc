# AAFC 서비스 안정성 계획서

> 작성일: 2026-02-18
> 목적: AWS 배포 전 서비스 중단 예방 조치 (코드 수정 + AWS 설정)

---

## 요약: 우리 서비스 데이터 규모

| 테이블 | 건수 | 위험도 |
|--------|------|--------|
| ~~DailyTotalData~~ | ~~5,094,089~~ | ~~🔴 매우 높음~~ **(모델 제거됨 - commit 6987103)** |
| ~~DailyCoachDataNew~~ | ~~574,419~~ | ~~🔴 높음~~ **(뷰 미사용 - commit 5fe7879, 모델 제거 예정)** |
| EnrollmentCourse | 220,596 | 🔴 높음 |
| Attendance | 231,147 | 🟡 중간 |
| SMSLog | 209,307 | 🟡 중간 |
| Enrollment | 79,490 | 🟡 중간 |
| PointHistory | 29,475 | 🟢 낮음 |

t2.micro (RAM 1GB) 기준으로 대용량 쿼리 하나가 전체 서비스를 멈출 수 있음.
> ✅ DailyTotalData(5백만건) 모델 제거, DailyCoachData/New/Month(68만건) 뷰 미사용으로 전환되어 주요 위험 요소 해소됨.
> 코치별현황 4개 리포트는 Enrollment 원본 테이블에서 실시간 직접 조회 (commit 5fe7879).

---

## 유형 1. 느린 쿼리로 인한 DB 과부하

### 원인
인덱스 없는 컬럼에 WHERE/ORDER BY 적용 시 풀스캔(Full Table Scan) 발생.
5백만 건 테이블에서 풀스캔 한 번 = DB CPU 100% 점유 → 다른 요청 모두 대기.

### 핵심 배경: MSSQL 원본도 인덱스가 없었다

원본 ASP + MSSQL을 직접 조회한 결과:

| MSSQL 테이블 | Django 모델 | 건수 | MSSQL 인덱스 현황 |
|---|---|---|---|
| lf_fcjoin_master | Enrollment | 79,490 | PK만 존재 |
| **lf_fcjoin_course** | **EnrollmentCourse** | **220,596** | **인덱스 없음 (HEAP)** |
| **lf_fcjoin_bill** | **EnrollmentBill** | - | **인덱스 없음 (HEAP)** |
| **lf_student_attendance** | **Attendance** | **231,147** | **인덱스 없음 (HEAP)** |
| lf_change_history | ChangeHistory | 877 | PK만 존재 |
| lf_wait_student | WaitStudent | - | PK만 존재 |
| em_mmt_tran_log_kyt | SMSLog | 209,307 | PK만 존재 |
| lf_member | Member | - | PK만 존재 |
| lf_memberchild | MemberChild | - | PK만 존재 |

**원본 ASP도 인덱스 없이 운영했음** → MSSQL의 Clustered Index(PK 순 물리 정렬)가 보완해줬지만 느렸을 것.
PostgreSQL은 Heap 구조이므로 인덱스 없으면 MSSQL보다 더 느림.
**인덱스를 추가하면 원본 ASP보다 확연히 빨라짐.**

### ASP WHERE 절 패턴 분석 결과

원본 ba_office 전체 ASP 파일을 분석하여 실제 사용 패턴을 확인함:

| 모델 | 가장 빈번한 WHERE 패턴 | 비고 |
|---|---|---|
| Enrollment | `del_chk='N' AND lecture_stats='LY'` | 거의 모든 조회에 포함 |
| Enrollment | `member_id`, `child_id` | 조인 기준 |
| Enrollment | `lecture_stats IN('LY','LP','PN')` | 상태별 필터 |
| EnrollmentCourse | `no_seq=?` (FK) | Django FK 자동 인덱스 ✅ |
| EnrollmentCourse | `bill_code IN('1001','1003')` | 청구항목 필터 |
| EnrollmentCourse | `course_ym`, `lecture_code` | 월별/강좌별 조회 |
| Attendance | `lecture_code + attendance_dt` | 복합 조회 (이미 있음 ✅) |
| WaitStudent | `del_chk='N' AND trans_gbn='N'` | 목록 조회 필수 조건 |
| WaitStudent | `sta_code`, `lecture_code` | 구장/강좌별 필터 |
| Member | `name`, `phone` LIKE 검색 | 관리자 회원 검색 |
| MemberChild | `course_state`, `sta_code` | 수강생 목록 필터 |
| SMSLog | ba_office에서 직접 조회 없음 | ⬇ 우선순위 낮음 |

### 현재 Django 모델 인덱스 현황

**이미 완료 (추가 불필요):**
- `Attendance`: lecture_code+attendance_dt, child_id, attendance_dt, sta_code ✅
- ~~`DailyTotalData`: proc_dt, member_id, sta_name, course_ym, pay_stats~~ **(모델 제거됨)**
- ~~`DailyCoachData/New/Month`: course_ym, proc_dt~~ **(뷰 미사용, 모델 제거 예정)**
- `MonthlyData`: proc_dt, sta_code ✅
- `EnrollmentCourse.enrollment_id` (FK → Django 자동 인덱스 생성) ✅

**추가 필요:**

| 모델 | 추가할 인덱스 | ASP 근거 |
|---|---|---|
| Enrollment | del_chk+lecture_stats 복합 | 목록 조회 필수 조건 |
| Enrollment | lecture_stats+pay_stats 복합 | 상태 필터 |
| Enrollment | member_id, child_id | 조인/상세 조회 |
| EnrollmentCourse | bill_code | 청구항목 필터 |
| EnrollmentCourse | course_ym, lecture_code | 월별/강좌별 |
| EnrollmentCourse | course_ym+lecture_code 복합 | 복합 조건 조회 |
| EnrollmentBill | bill_code, pay_stats | 청구항목/결제상태 |
| WaitStudent | del_chk+trans_gbn 복합 | 목록 필수 조건 |
| WaitStudent | sta_code, lecture_code | 구장/강좌 필터 |
| Member | name, phone | 관리자 검색 |
| MemberChild | course_state, sta_code | 수강생 목록 |
| MemberChild | sta_code+course_state 복합 | 복합 조건 |

### 조치: 인덱스 추가 (코드 수정 필요)

#### apps/enrollment/models.py

```python
class Enrollment(models.Model):
    # ... 기존 필드들 ...
    class Meta:
        db_table = 'enrollment_enrollment'
        ordering = ['-id']
        indexes = [
            # 목록 조회 필수 조건 (del_chk='N' AND lecture_stats=?)
            models.Index(fields=['del_chk', 'lecture_stats'], name='idx_enroll_delchk_stats'),
            # 상태 복합 필터
            models.Index(fields=['lecture_stats', 'pay_stats'], name='idx_enroll_lec_pay_stats'),
            # 회원/자녀 기준 조회
            models.Index(fields=['member_id'], name='idx_enroll_member'),
            models.Index(fields=['child_id'], name='idx_enroll_child'),
        ]


class EnrollmentCourse(models.Model):
    # ... 기존 필드들 ...
    # enrollment_id (FK)는 Django가 자동으로 인덱스 생성 → 별도 불필요
    class Meta:
        db_table = 'enrollment_enrollmentcourse'
        indexes = [
            # 청구항목 필터 (bill_code IN ('1001','1003'))
            models.Index(fields=['bill_code'], name='idx_ec_bill_code'),
            # 월별 조회
            models.Index(fields=['course_ym'], name='idx_ec_course_ym'),
            # 강좌별 조회
            models.Index(fields=['lecture_code'], name='idx_ec_lec_code'),
            # 월별+강좌 복합 조회
            models.Index(fields=['course_ym', 'lecture_code'], name='idx_ec_ym_lec'),
        ]


class EnrollmentBill(models.Model):
    # ... 기존 필드들 ...
    # enrollment_id (FK)는 Django가 자동으로 인덱스 생성
    class Meta:
        db_table = 'enrollment_enrollmentbill'
        indexes = [
            models.Index(fields=['bill_code'], name='idx_bill_code'),
            models.Index(fields=['pay_stats'], name='idx_bill_pay_stats'),
        ]


class WaitStudent(models.Model):
    # ... 기존 필드들 ...
    class Meta:
        db_table = 'enrollment_waitstudent'
        indexes = [
            # 목록 조회 필수 조건 (del_chk='N' AND trans_gbn='N')
            models.Index(fields=['del_chk', 'trans_gbn'], name='idx_wait_delchk_trans'),
            # 구장/강좌별 필터
            models.Index(fields=['sta_code', 'lecture_code'], name='idx_wait_sta_lec'),
        ]
```

#### apps/accounts/models.py

```python
class Member(models.Model):
    # ... 기존 필드들 ...
    class Meta:
        db_table = 'accounts_member'
        indexes = [
            # 관리자 회원 검색 (name LIKE, phone LIKE)
            models.Index(fields=['name'], name='idx_member_name'),
            models.Index(fields=['phone'], name='idx_member_phone'),
        ]


class MemberChild(models.Model):
    # ... 기존 필드들 ...
    class Meta:
        db_table = 'accounts_memberchild'
        indexes = [
            # 수강생 목록 필터
            models.Index(fields=['course_state'], name='idx_child_course_state'),
            models.Index(fields=['sta_code'], name='idx_child_sta_code'),
            # 구장+상태 복합 (수강생 관리 핵심 필터)
            models.Index(fields=['sta_code', 'course_state'], name='idx_child_sta_state'),
        ]
```

> ℹ️ SMSLog: ba_office에서 직접 조회하지 않으므로 인덱스 추가 불필요 (ordering 필드는 PK 기반으로 충분)

### 실행 명령

```bash
# 로컬에서 마이그레이션 파일 생성 후 GitHub push
python manage.py makemigrations enrollment accounts --settings=config.settings.local
python manage.py migrate --settings=config.settings.local

# 서버에서는 migrate만 실행
python manage.py migrate --settings=config.settings.prod
```

> ⚠️ 대용량 테이블(220K, 231K건) 인덱스 생성은 수 분 소요 가능 → 서비스 오픈 전 새벽에 실행 권장

---

## 유형 2. DB 커넥션 고갈

### 원인
Django 기본 설정은 요청마다 DB 커넥션을 새로 생성하고 닫음.
수강신청 기간 동시 접속 급증 시 RDS 커넥션 한도 초과 → 새 연결 거부.

RDS db.t3.micro 기본 max_connections: 약 **60~80개**

### 조치: settings/prod.py 수정 필요

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ... 기존 설정 ...
        'CONN_MAX_AGE': 60,        # 커넥션 60초간 재사용 (기본값 0 = 매번 새로 생성)
        'OPTIONS': {
            'connect_timeout': 10, # 연결 타임아웃 10초
            'options': '-c statement_timeout=30000',  # 쿼리 30초 초과 시 자동 중단
        },
    }
}
```

### 효과
- `CONN_MAX_AGE=60`: 커넥션 재사용으로 RDS 부하 60~80% 감소
- `statement_timeout=30000`: 30초 이상 걸리는 쿼리 자동 Kill → DB 잠금 방지

---

## 유형 3. 대용량 쿼리로 인한 메모리 부족 (OOM)

### 원인
t2.micro RAM 1GB. 관리자 리포트가 수만 건을 한 번에 메모리에 올리면
Gunicorn worker 프로세스가 OOM Kill → 502 Bad Gateway 발생.

### 현재 코드 분석

**이미 제한 있는 곳 (양호):**
- `views.py:686` → `[:10000]` 제한 있음
- `views.py:2782` → `[:10000]` 제한 있음

**확인 필요한 리포트 뷰:**
- ~~`apps/office/views_report.py` 내 DailyTotalData 직접 조회 구간~~ **(모델 제거됨, 해당 없음)**

### 조치: views_report.py 에서 대용량 조회 패턴 확인

> DailyTotalData(5백만건)는 모델 자체가 제거되어 OOM 최대 위험 요소 해소.
> 나머지 리포트 뷰도 기존 `[:10000]` 제한이 적용되어 있어 양호.

### Gunicorn worker 설정으로 OOM 방어

```ini
# /etc/systemd/system/gunicorn.service
ExecStart=/srv/aafc/venv/bin/gunicorn \
    --workers 2 \           # t2.micro는 2개가 적정 (3개면 메모리 부족)
    --timeout 120 \         # 120초 초과 요청 자동 Kill
    --max-requests 1000 \   # 1000 요청 처리 후 worker 재시작 (메모리 누수 방지)
    --max-requests-jitter 100 \
    --bind unix:/srv/aafc/gunicorn.sock \
    config.wsgi:application
```

---

## 유형 4. RDS 스토리지 포화

### 원인
미디어 파일, 로그 등이 쌓여 RDS 스토리지 100% 도달 → DB 쓰기 완전 불가.

### 조치: AWS 콘솔에서 설정

1. RDS → 데이터베이스 선택 → 수정
2. **스토리지 자동 조정 활성화** 체크
3. 최대 스토리지 임계값: **100GB** 설정
4. CloudWatch 알람: 스토리지 80% 도달 시 이메일 알림

> 비용: 추가 스토리지 $0.115/GB/월 (gp2 기준)

---

## 유형 5. AWS RDS 자동 백업 중 순간 중단

### 원인
RDS 자동 백업 실행 시 약 수 초~수십 초 지연 발생.
기본 설정 시 업무 시간 중에 백업이 실행될 수 있음.

### 조치: AWS 콘솔에서 설정

1. RDS → 유지 관리 및 백업
2. **백업 보존 기간**: 7일
3. **백업 기간**: `18:00 UTC ~ 18:30 UTC` (한국시간 새벽 3:00 ~ 3:30)
4. **유지 관리 기간**: `Mon:19:00 UTC ~ Mon:19:30 UTC` (한국시간 새벽 4:00)

---

## 유형 6. EC2 서버 재시작 후 서비스 미복구

### 원인
AWS 프리 티어 EC2는 가끔 재시작됨. systemd 서비스 미등록 시
재시작 후 Gunicorn/Nginx가 자동 구동되지 않아 서비스 중단.

### 조치: 서비스 자동 시작 등록

```bash
sudo systemctl enable gunicorn   # EC2 재시작 시 자동 시작
sudo systemctl enable nginx      # EC2 재시작 시 자동 시작
```

배포 시 반드시 확인:
```bash
sudo systemctl is-enabled gunicorn  # "enabled" 출력 확인
sudo systemctl is-enabled nginx     # "enabled" 출력 확인
```

---

## 유형 7. 정적 파일 미수집으로 인한 CSS/JS 깨짐

### 원인
`DEBUG=False` 상태에서 Django는 정적 파일을 직접 서빙하지 않음.
`collectstatic` 미실행 또는 Nginx 경로 오설정 시 CSS/JS 전부 404.

### 조치

```bash
# 코드 배포 후 반드시 실행
python manage.py collectstatic --settings=config.settings.prod --noinput

# settings/prod.py 에 반드시 추가
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Nginx 설정 확인:
```nginx
location /static/ {
    alias /srv/aafc/staticfiles/;  # STATIC_ROOT 경로와 일치해야 함
}
```

---

## 유형 8. 세션/결제 트랜잭션 락

### 현재 상태: 이미 처리됨 (추가 조치 불필요)

- `payments/views.py`: `@transaction.atomic` 적용 → 결제 실패 시 자동 롤백
- `shop/views.py`: `@transaction.atomic` 적용

단, 결제 중 중단된 트랜잭션 정리를 위해 PostgreSQL 설정:
```sql
-- RDS에서 실행 (30분 이상 idle 트랜잭션 자동 종료)
-- RDS 파라미터 그룹에서 설정
idle_in_transaction_session_timeout = 1800000  -- 30분 (ms)
```

---

## 전체 조치 실행 체크리스트

### A. 코드 수정 (배포 전, 로컬에서)

**인덱스 추가 (ASP WHERE 패턴 분석 기반):**
- [ ] `apps/enrollment/models.py` → Enrollment: del_chk+lecture_stats, lecture_stats+pay_stats, member_id, child_id
- [ ] `apps/enrollment/models.py` → EnrollmentCourse: bill_code, course_ym, lecture_code, course_ym+lecture_code
- [ ] `apps/enrollment/models.py` → EnrollmentBill: bill_code, pay_stats
- [ ] `apps/enrollment/models.py` → WaitStudent: del_chk+trans_gbn, sta_code+lecture_code
- [ ] `apps/accounts/models.py` → Member: name, phone
- [ ] `apps/accounts/models.py` → MemberChild: course_state, sta_code, sta_code+course_state
- [ ] `python manage.py makemigrations enrollment accounts` 실행 후 GitHub push

**설정 추가:**
- [ ] `config/settings/prod.py` - CONN_MAX_AGE=60, statement_timeout 추가
- [ ] `config/settings/prod.py` - STATIC_ROOT 추가
- [ ] GitHub push

### B. EC2 서버 설정

- [ ] gunicorn.service - workers=2, timeout=120, max-requests=1000 설정
- [ ] `sudo systemctl enable gunicorn`
- [ ] `sudo systemctl enable nginx`

### C. AWS 콘솔 설정

- [ ] RDS: 스토리지 자동 조정 활성화 (최대 100GB)
- [ ] RDS: 백업 시간 새벽 3시로 설정
- [ ] RDS: 유지 관리 시간 새벽 4시로 설정
- [ ] RDS 파라미터 그룹: `idle_in_transaction_session_timeout = 1800000`
- [ ] CloudWatch: RDS 스토리지 80% 알람 + 이메일 설정
- [ ] CloudWatch: EC2 CPU 80% 알람 + 이메일 설정

### D. 서버 배포 후 검증

- [ ] `python manage.py migrate` → 인덱스 생성 확인
- [ ] `python manage.py collectstatic` → staticfiles/ 생성 확인
- [ ] 브라우저에서 CSS/JS 정상 로드 확인
- [ ] 관리자 리포트 페이지 응답 시간 확인 (5초 이내)
- [ ] `sudo systemctl status gunicorn` → active 확인
- [ ] EC2 재시작 후 서비스 자동 복구 확인

---

## 우선순위 정리

| 순위 | 유형 | 작업 위치 | 영향도 |
|------|------|-----------|--------|
| 1 | 인덱스 추가 | 코드 (models.py) | 🔴 쿼리 속도 결정적 |
| 2 | CONN_MAX_AGE + statement_timeout | 코드 (prod.py) | 🔴 커넥션 안정성 |
| 3 | Gunicorn workers=2 + timeout | EC2 서버 설정 | 🔴 OOM 방지 |
| 4 | RDS 자동 백업 시간 | AWS 콘솔 | 🟡 업무시간 영향 제거 |
| 5 | RDS 스토리지 자동 조정 | AWS 콘솔 | 🟡 장기 운영 안전 |
| 6 | systemctl enable | EC2 서버 설정 | 🟡 재시작 복구 |
| 7 | CloudWatch 알람 | AWS 콘솔 | 🟢 모니터링 |
| 8 | idle_in_transaction_session_timeout | RDS 파라미터 | 🟢 트랜잭션 정리 |
