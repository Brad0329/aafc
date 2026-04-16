# AAFC 운영 관리 가이드

> 최종 수정: 2026-04-16
> 환경: EC2 (Ubuntu 22.04) + RDS PostgreSQL 17 + S3

---

## 배포 구성

```
인터넷
  │
  ▼
EC2 (Ubuntu 22.04, t3.micro)
  ├── Nginx (80포트, 리버스 프록시 + 정적파일)
  └── Gunicorn (Unix Socket, Django WSGI)
        │
        ├── RDS PostgreSQL 17 (aafc_prod DB)
        └── S3 (aafc-bucket, 미디어 파일)
```

---

## AWS 리소스 정보

| 서비스 | 이름 | 비고 |
|--------|------|------|
| EC2 | aafc-server | t3.micro, Ubuntu 22.04 LTS |
| RDS | aafc-db | PostgreSQL 17, db.t3.micro |
| S3 | aafc-bucket | 미디어 파일 (media/ 동기화) |
| 보안 그룹 | launch-wizard-1 | EC2용 (SSH:내IP, HTTP:80, HTTPS:443) |

- EC2 퍼블릭 IP: `43.201.113.91`
- RDS 엔드포인트: `aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com`
- S3 URL: `https://aafc-bucket.s3.ap-northeast-2.amazonaws.com/`
- PEM 키: `C:\Users\user\Downloads\aafc-key.pem`

---

## 접속 URL

| 항목 | URL |
|------|-----|
| AWS 콘솔 | https://console.aws.amazon.com (pesseq@gmail.com) |
| 메인 사이트 | http://43.201.113.91 |
| 관리자 페이지 | http://43.201.113.91/ba_office/ |
| 관리자 계정 | junior2019 / test1234 |

---

## EC2 서버 접속

```powershell
# 로컬 PowerShell
ssh -i "C:\Users\user\Downloads\aafc-key.pem" ubuntu@43.201.113.91
```

> SSH 접속 안 될 경우: EC2 보안 그룹 → launch-wizard-1 → 인바운드 규칙 → SSH 22번 소스를 "내 IP"로 변경

---

## 서버 구성 정보

| 항목 | 경로/값 |
|------|---------|
| 프로젝트 경로 | `/srv/aafc` |
| 가상환경 | `/srv/aafc/venv` |
| 환경변수 파일 | `/srv/aafc/.env` |
| 정적파일 | `/srv/aafc/staticfiles` |
| Gunicorn 서비스 | `/etc/systemd/system/gunicorn.service` |
| Nginx 설정 | `/etc/nginx/sites-available/aafc` |

---

## 코드 업데이트 절차

### 일반 코드 변경
```bash
# 1. 로컬에서 수정 후 GitHub push
git add 파일명
git commit -m "변경 내용"
git push origin main

# 2. EC2에서 pull 및 재시작
cd /srv/aafc && git pull && sudo systemctl restart gunicorn
```

### 정적파일(CSS/JS/이미지) 변경 시
```bash
# EC2에서 추가 실행
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

### DB 모델 변경 시 (migrations)
```bash
# 로컬에서
python manage.py makemigrations
python manage.py migrate        # 로컬 확인 후
git push origin main

# EC2에서
git pull
source venv/bin/activate
python manage.py migrate        # RDS에 적용
sudo systemctl restart gunicorn
```

### 미디어 파일 추가 시 (S3)
```powershell
# 로컬 PowerShell에서
aws s3 sync "C:\Users\user\Documents\aafc\media" s3://aafc-bucket/ --region ap-northeast-2
```

---

## 서비스 관리 명령어

```bash
# Gunicorn 상태/재시작
sudo systemctl status gunicorn
sudo systemctl restart gunicorn

# Nginx 상태/재시작
sudo systemctl status nginx
sudo systemctl reload nginx

# 디스크 사용량
df -h /

# 로그 확인
sudo journalctl -u gunicorn -n 50 --no-pager
sudo journalctl -u gunicorn --since "1 hour ago"
sudo tail -f /var/log/nginx/error.log
```

---

## 관리자 페이지 (/ba_office) IP 제한

허용 IP를 변경해야 할 때 (예: 사무실/집 IP 변경):

```bash
# EC2에서
sudo nano /etc/nginx/sites-available/aafc

# /ba_office location 블록에서 IP 수정
# allow 1.2.3.4;  <- 여기 변경

sudo nginx -t                    # 설정 문법 확인
sudo systemctl reload nginx      # 적용
```

> **주의**: 가정용 인터넷은 IP가 수시로 변경될 수 있음. 현재 IP 확인: https://www.whatismyip.com

---

## DB 데이터 이관 (실서비스 MSSQL → 로컬 PostgreSQL → AWS RDS)

### 전체 흐름

```
실서비스 .bak 파일 → MSSQL 복원 → 마이그레이션 스크립트 14개 → 로컬 PostgreSQL → pg_dump → EC2 → RDS
```

### Step 1: MSSQL에 .bak 파일 복원

```bash
# .bak 파일을 MSSQL이 접근 가능한 경로에 복사
cp "원본.bak" "C:\temp\2018_junior.bak"

# Windows 인증으로 복원 (juni_db 계정은 RESTORE 권한 없음)
sqlcmd -S "localhost\SQLEXPRESS" -E -Q "
ALTER DATABASE [2018_junior] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
RESTORE DATABASE [2018_junior] FROM DISK = N'C:\temp\2018_junior.bak'
WITH REPLACE,
MOVE '2018_junior' TO 'C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\DATA\2018_junior.mdf',
MOVE '2018_junior_log' TO 'C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\DATA\2018_junior_log.ldf';
ALTER DATABASE [2018_junior] SET MULTI_USER;
"
```

> **주의**: 복원 후 juni_db 사용자 매핑이 깨짐 → 아래 명령으로 재설정 필요
```bash
sqlcmd -S "localhost\SQLEXPRESS" -E -d 2018_junior -Q "
ALTER AUTHORIZATION ON DATABASE::[2018_junior] TO sa;
IF EXISTS (SELECT * FROM sys.database_principals WHERE name = 'juni_db')
  DROP USER juni_db;
CREATE USER juni_db FOR LOGIN juni_db;
EXEC sp_addrolemember 'db_owner', 'juni_db';
"
```

### Step 2: 로컬 PostgreSQL 초기화 + 마이그레이션 스크립트 실행

```bash
# PostgreSQL 스키마 초기화
psql -U postgres -d aafc_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres;"

# Django 테이블 재생성
python manage.py migrate --settings=config.settings.local

# 마이그레이션 스크립트 순서대로 실행 (부모 테이블 먼저!)
python scripts/migrate_common.py          # 공통코드
python scripts/migrate_members.py         # 회원+자녀
python scripts/migrate_courses.py         # 구장/코치/강좌
python scripts/migrate_course_src.py      # 강좌 추가 데이터
python scripts/migrate_enrollment.py      # 수강신청 (30만건+, 10분 이상 소요)
python scripts/migrate_board.py           # 게시판
python scripts/migrate_consult.py         # 상담
python scripts/migrate_shop.py            # 쇼핑몰
python scripts/migrate_points.py          # 포인트
python scripts/migrate_notifications.py   # 알림/SMS (20만건, 5분 소요)
python scripts/migrate_reports.py         # 리포트/출석 (23만건, 5분 소요)
python scripts/migrate_training.py        # 훈련일정
python scripts/migrate_office.py          # 관리자계정
python scripts/migrate_popup.py           # 팝업

# Django superuser 재생성
python manage.py createsuperuser  # admin / admin1234
```

### Step 3: 로컬 PostgreSQL → AWS RDS

```powershell
# 1. dump 생성 (파일명에 날짜 포함 권장 - 이전 파일과 혼동 방지)
& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres -d aafc_dev -F c -f C:\Users\user\Downloads\aafc_dump_YYYYMMDD.dump

# 2. EC2로 전송
scp -i "C:\Users\user\Downloads\aafc-key.pem" "C:\Users\user\Downloads\aafc_dump_YYYYMMDD.dump" ubuntu@43.201.113.91:/srv/aafc/aafc_dump.dump
```

```bash
# 3. EC2에서 RDS로 복원 (비밀번호는 /srv/aafc/.env의 DB_PASSWORD 참조)
# --no-owner 필수! (RDS에 postgres role이 없어서 OWNER 에러 발생)
PGPASSWORD='비밀번호' pg_restore -h aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com -U aafc_user -d aafc_prod -F c --clean --if-exists --no-owner /srv/aafc/aafc_dump.dump

# 4. Gunicorn 재시작
sudo systemctl restart gunicorn
```

### 이관 후 검증 쿼리

```bash
# RDS 접속하여 주요 테이블 건수 확인
PGPASSWORD='비밀번호' psql -h aafc-db...amazonaws.com -U aafc_user -d aafc_prod -c "
SELECT 'Member' AS tbl, COUNT(*) FROM accounts_member UNION ALL
SELECT 'Enrollment', COUNT(*) FROM enrollment_enrollment UNION ALL
SELECT 'EnrollmentCourse', COUNT(*) FROM enrollment_enrollmentcourse UNION ALL
SELECT 'Attendance', COUNT(*) FROM enrollment_attendance
ORDER BY count DESC;
"
```

### DB 이관 주의사항

| 항목 | 설명 |
|------|------|
| .bak 파일 경로 | `C:\Program Files\` 하위는 권한 문제 → `C:\temp\`에 복사 후 복원 |
| MSSQL 복원 후 | juni_db 사용자 매핑 반드시 재설정 (위 명령 참조) |
| pg_restore 필수 옵션 | `--no-owner` 없으면 "role postgres does not exist" 에러 64건 발생 |
| dump 파일명 | 날짜 포함 권장 (`aafc_dump_20260416.dump`) - 이전 파일과 혼동 방지 |
| 소요 시간 | 전체 약 30~40분 (enrollment/notifications/reports가 대부분) |
| migrate_reports.py | DailyTotalData 등 4개 모델 제거됨 - Attendance/ChangeHistory/MonthlyData만 이관 |

---

## RDS DB 관련

### 로컬에서 RDS 직접 접속
```bash
psql -h aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com -U aafc_user -d aafc_prod
```

### RDS 백업 (수동)
```bash
pg_dump -h aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com -U aafc_user -d aafc_prod -Fc -f aafc_backup_YYYYMMDD.dump
```

### RDS 백업 설정
- AWS 콘솔 → RDS → aafc-db → 수정
- 백업 보존 기간: 7일
- 백업 기간: 18:00-19:00 UTC (= 한국시간 새벽 3시)

---

## CloudWatch 알람

| 알람명 | 조건 | 의미 |
|--------|------|------|
| `aafc-rds-cpu-high` | CPU > 80% | DB 과부하 경고 |
| `aafc-rds-storage-low` | 여유공간 < 2GB | 디스크 부족 경고 |

알람 발생 시 이메일 수신 → 즉시 AWS 콘솔에서 원인 확인

---

## .env 파일 구조 (EC2 서버)

```ini
DJANGO_SECRET_KEY=...
DJANGO_SETTINGS_MODULE=config.settings.prod
ALLOWED_HOSTS=43.201.113.91

DB_NAME=aafc_prod
DB_USER=aafc_user
DB_PASSWORD=...
DB_HOST=aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com
DB_PORT=5432

AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=aafc-bucket
AWS_S3_REGION_NAME=ap-northeast-2
```

> **주의**: .env 파일은 Git에 포함되지 않음. 서버 직접 수정 필요.

---

## 운영 주의사항

1. **EC2 재시작 시 IP 변경**: EC2를 중지/시작하면 퍼블릭 IP가 바뀜 → Nginx IP 제한 설정, DNS 등 업데이트 필요 (고정 IP 필요 시 Elastic IP 할당)
2. **SSH 접속 안 될 때**: EC2 보안 그룹 → 인바운드 규칙 → SSH 소스를 "내 IP"로 재설정
3. **미디어 파일**: EC2 로컬이 아닌 S3에 저장됨. 새 미디어 파일은 반드시 S3 sync 필요
4. **정적 파일**: EC2의 `/srv/aafc/staticfiles/`에 저장. 변경 시 collectstatic 실행
5. **DB 마이그레이션**: 로컬에서 확인 후 EC2에서 재실행. RDS는 되돌리기 어려우므로 신중하게
6. **settings**: EC2는 `config.settings.prod` 사용. 로컬은 `config.settings.local`

---

## 배포 시 트러블슈팅 이력

| 문제 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError: openpyxl` | requirements.txt 누락 | `pip install openpyxl` + requirements.txt 추가 |
| DB 연결 시 localhost 접속 | manage.py 기본 settings가 local | `--settings=config.settings.prod` 명시 또는 `~/.bashrc`에 `export DJANGO_SETTINGS_MODULE=config.settings.prod` 추가 |
| `pg_restore: unsupported version (1.15)` | EC2 postgresql-client 버전이 낮음 | EC2에 postgresql-client-17 설치 |
| 이미지 URL이 EC2 IP로 요청됨 | 템플릿에 `/fcdata/` 하드코딩 | `{{ MEDIA_URL }}fcdata/`로 변경 |
| `{{ MEDIA_URL }}` 템플릿에서 빈값 | context_processors 누락 | `django.template.context_processors.media` 추가 |

---

## 코드 리빌딩 대상 (향후 작업)

기능상 문제는 없으나 유지보수를 위해 리팩토링이 필요한 파일 목록.
**기능 추가 작업이 모두 끝난 후** 진행 권장.

### 우선순위 1 - office 앱 분할 (긴급)

| 파일 | 현재 라인 수 | 문제 |
|------|------------|------|
| `apps/office/views.py` | 5,359줄 / 113개 함수 | 단일 파일에 모든 관리자 뷰 혼재 |
| `apps/office/urls.py` | 268줄 / 174개 URL | 단일 파일에 모든 URL 혼재 |

**분할 방향**:
```
views.py      → views_member.py   (회원관리: member_*, child_*)
              → views_student.py  (수강생관리: student_*, master_*, wait_*)
              → views_consult.py  (상담관리: consult_*)
              → views_course.py   (과정관리: stadium_*, coach_*, lecture_*)
              → views_system.py   (시스템관리: admin_*, code_*)

urls.py       → urls_member.py
              → urls_student.py
              → urls_consult.py
              → urls_course.py
              → urls_system.py
```

### 우선순위 2 - 공통 유틸 추출

- `apps/office/utils.py` 생성 → 반복되는 Paginator 로직(11회), 필터링 패턴(351회) 헬퍼 함수로 추출
- `apps/office/views_report.py` (2,990줄) → 보조 헬퍼 함수 분리

### 우선순위 3 - 대형 템플릿 분할

| 템플릿 | 라인 수 | 처리 |
|--------|---------|------|
| `lfstudent/student_detail.html` | 522줄 | includes로 분할 |
| `lfstudent/student_add.html` | 408줄 | includes로 분할 |
| `lfcourse/promotion_input.html` | 336줄 | 부분 템플릿화 |

### 현재 양호한 파일 (리빌딩 불필요)

- `apps/shop/models.py` 419줄 - 모델 수가 많아 자연스러운 크기
- `apps/enrollment/views.py` 654줄 - 적당한 크기
- `apps/office/views_shop.py` 664줄 - 적당한 크기
- `apps/office/views_portal.py` 545줄 - 적당한 크기

---

## 보안 점검 결과

### 안전한 항목

| 항목 | 상태 | 근거 |
|------|------|------|
| SQL Injection | 안전 | Django ORM + Raw SQL도 `%s` 파라미터 바인딩 사용 |
| XSS | 안전 | Django 템플릿 자동 이스케이프, `mark_safe()` 미사용 |
| CSRF | 안전 | Django CSRF 미들웨어 적용 |
| 민감정보 노출 | 안전 | `.env` 파일 분리, Git 미포함 |
| 관리자 인증 우회 | 안전 | `@office_login_required` 데코레이터 전체 적용 |

### 취약점

**파일 업로드 확장자 검증 없음**

해당 위치:
- `apps/office/views_portal.py` - 팝업 이미지, 게시판 이미지/첨부파일
- `apps/office/views.py` - 구장 이미지, 코치 이미지

현재 확장자/MIME 타입 검증 없이 업로드 허용.
단, **관리자 페이지 로그인 후에만 업로드 가능** + **IP 제한 적용 시** 위험도 매우 낮음.

향후 보완 시 추가할 검증 코드 (예시):
```python
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
ext = f.name.rsplit('.', 1)[-1].lower()
if ext not in ALLOWED_EXTENSIONS:
    # 에러 처리
```
