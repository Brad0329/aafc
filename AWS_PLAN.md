# AAFC Django AWS 배포 계획서

> 작성일: 2026-02-18
> 환경: EC2 (Ubuntu 22.04) + RDS PostgreSQL + S3 (미디어 파일)
> 리전: ap-northeast-2 (서울)

---

## 전체 구성도

```
인터넷
  │
  ▼
[Route 53] (도메인, 선택사항)
  │
  ▼
[EC2 - Ubuntu 22.04]
  ├── Nginx (80/443 포트, 리버스 프록시)
  └── Gunicorn (Unix Socket, Django WSGI)
        │
        ├── [RDS PostgreSQL] (DB, 5432 포트 - EC2에서만 접근)
        └── [S3 Bucket] (media 파일 500MB, 업로드/서빙)
```

---

## ⚠️ 서비스 안정성 사전 조치 (배포 전 필수)

> 상세 내용: **[AWS_SERVICE_STABILITY.md](AWS_SERVICE_STABILITY.md)** 참조

배포 전 코드 수정 + AWS 설정이 선행되어야 합니다.

| 순위 | 조치 | 파일 | 완료 |
|------|------|------|------|
| 1 | Enrollment/EnrollmentCourse/EnrollmentBill/WaitStudent 인덱스 추가 | apps/enrollment/models.py | [ ] |
| 2 | Member/MemberChild 인덱스 추가 | apps/accounts/models.py | [ ] |
| 3 | makemigrations 실행 + GitHub push | 로컬 터미널 | [ ] |
| 4 | CONN_MAX_AGE=60 + statement_timeout 추가 | config/settings/prod.py | [ ] |
| 5 | Gunicorn workers=2, timeout=120, max-requests=1000 | EC2 gunicorn.service | [ ] |
| 6 | RDS: 스토리지 자동 조정 + 백업 새벽 3시 | AWS 콘솔 | [ ] |
| 7 | systemctl enable gunicorn/nginx | EC2 | [ ] |
| 8 | CloudWatch CPU/스토리지 알람 설정 | AWS 콘솔 | [ ] |

---

## 사전 체크리스트

- [x] GitHub 레포: https://github.com/Brad0329/aafc.git
- [x] Django settings 분리 구조 (base.py + local.py)
- [ ] **서비스 안정성 조치 완료** (AWS_SERVICE_STABILITY.md)
- [ ] settings/prod.py 생성
- [ ] requirements.txt 정리 (gunicorn, whitenoise, boto3 등 추가)
- [ ] .env 환경변수 구조 설계
- [ ] GitHub에 최신 코드 push

---

## PHASE 1. 코드 준비 (로컬 작업)

### 1-1. requirements.txt 정리

현재 3개 패키지만 있음 → 아래로 교체:

```
# 현재
django==5.2.11
psycopg2-binary==2.9.11
pyodbc==5.3.0          ← 프로덕션 불필요 (MSSQL 마이그레이션용)

# 추가 필요
gunicorn               # WSGI 서버
whitenoise             # 정적파일 서빙 (선택, S3 미사용 시)
boto3                  # S3 연동
django-storages        # S3 파일 스토리지
python-decouple        # .env 환경변수 읽기
```

> ⚠️ pyodbc는 MSSQL 마이그레이션 전용 → requirements_dev.txt로 분리

### 1-2. .env 파일 구조

```ini
# .env (로컬 + 서버 공통 구조, 값은 서버마다 다름)
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.prod

DB_NAME=aafc_prod
DB_USER=aafc_user
DB_PASSWORD=your-db-password
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432

AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=aafc-media
AWS_S3_REGION_NAME=ap-northeast-2
```

> ⚠️ .env는 절대 GitHub에 push 금지 (.gitignore 확인 필수)

### 1-3. settings/prod.py 작성

```python
from .base import *
from decouple import config

SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = False

ALLOWED_HOSTS = [
    'your-ec2-ip',
    'your-domain.com',  # 도메인 있을 경우
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# 정적 파일
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic 결과물

# S3 미디어 파일
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ap-northeast-2')
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

# 보안 설정 (HTTPS 사용 시)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
```

### 1-4. wsgi.py 수정

```python
# config/wsgi.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
```

> 서버에서 환경변수로 덮어쓰므로 prod로 변경

### 1-5. .gitignore 확인

```
.env
*.env
staticfiles/
__pycache__/
*.pyc
venv/
```

### 1-6. GitHub push

```bash
git add requirements.txt config/settings/prod.py config/wsgi.py .gitignore
git commit -m "Add prod settings and update requirements for AWS deployment"
git push origin main
```

---

## PHASE 2. AWS 사전 설정

### 2-1. IAM 사용자 생성 (루트 계정 직접 사용 금지)

1. AWS 콘솔 → IAM → 사용자 → 사용자 생성
2. 이름: `aafc-admin`
3. 권한: `AdministratorAccess` (또는 필요 권한만)
4. 액세스 키 생성 → CSV 다운로드 (분실 시 재발급 불가)

### 2-2. S3 버킷 생성 (미디어 파일용)

1. S3 → 버킷 만들기
2. 버킷 이름: `aafc-media` (전 세계 유일해야 함)
3. 리전: ap-northeast-2 (서울)
4. 퍼블릭 액세스 차단: **모두 해제** (미디어 파일 공개 접근 필요)
5. 버킷 정책 추가:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::aafc-media/*"
     }]
   }
   ```
6. 로컬 media/ 폴더 (500MB) → S3에 업로드:
   ```bash
   aws s3 sync ./media/ s3://aafc-media/ --region ap-northeast-2
   ```

### 2-3. VPC 확인

- 기본 VPC 사용 (신규 계정 자동 생성됨)
- 리전: ap-northeast-2

---

## PHASE 3. RDS PostgreSQL 생성

### 3-1. 생성 설정

| 항목 | 값 |
|------|-----|
| 엔진 | PostgreSQL 16.x |
| 템플릿 | 프리 티어 |
| DB 인스턴스 식별자 | `aafc-db` |
| 마스터 사용자명 | `aafc_user` |
| 마스터 암호 | 강력한 비밀번호 설정 |
| 인스턴스 클래스 | `db.t3.micro` (프리 티어) |
| 스토리지 | 20GB gp2 |
| 퍼블릭 액세스 | **아니오** (EC2에서만 접근) |
| VPC 보안 그룹 | 새로 생성 `rds-aafc-sg` |
| 초기 데이터베이스 이름 | `aafc_prod` |

### 3-2. RDS 안정성 설정 (AWS_SERVICE_STABILITY.md 유형 4,5,8 참조)

| 항목 | 설정값 | 위치 |
|------|--------|------|
| 스토리지 자동 조정 | 활성화, 최대 100GB | RDS 수정 |
| 백업 보존 기간 | 7일 | 유지 관리 탭 |
| 백업 시간 | 18:00~18:30 UTC (새벽 3시 KST) | 유지 관리 탭 |
| 유지 관리 시간 | Mon 19:00~19:30 UTC (새벽 4시 KST) | 유지 관리 탭 |
| idle_in_transaction_session_timeout | 1800000 (30분) | 파라미터 그룹 |

**RDS 파라미터 그룹 설정:**
1. RDS → 파라미터 그룹 → 새 파라미터 그룹 생성 (postgres16)
2. `idle_in_transaction_session_timeout` = `1800000`
3. RDS 인스턴스에 파라미터 그룹 연결 → 재시작

### 3-3. RDS 보안 그룹 설정 (`rds-aafc-sg`)

| 유형 | 포트 | 소스 |
|------|------|------|
| PostgreSQL | 5432 | EC2 보안 그룹 ID (나중에 추가) |

> ⚠️ RDS 엔드포인트는 생성 후 확인 (예: `aafc-db.xxxxxxxxx.ap-northeast-2.rds.amazonaws.com`)

---

## PHASE 4. EC2 인스턴스 생성

### 4-1. 생성 설정

| 항목 | 값 |
|------|-----|
| 이름 | `aafc-server` |
| AMI | Ubuntu Server 22.04 LTS |
| 인스턴스 유형 | `t2.micro` (프리 티어) |
| 키 페어 | 새로 생성 `aafc-key` → .pem 다운로드 |
| 네트워크 | 기본 VPC |
| 퍼블릭 IP 자동 할당 | 활성화 |
| 보안 그룹 | 새로 생성 `ec2-aafc-sg` |
| 스토리지 | 20GB gp2 |

### 4-2. EC2 보안 그룹 설정 (`ec2-aafc-sg`)

**인바운드 규칙:**

| 유형 | 포트 | 소스 | 용도 |
|------|------|------|------|
| SSH | 22 | 내 IP | 서버 접속 |
| HTTP | 80 | 0.0.0.0/0 | 웹 서비스 |
| HTTPS | 443 | 0.0.0.0/0 | 웹 서비스 (SSL 시) |

> SSH 포트는 반드시 내 IP만 허용 (보안)

### 4-3. RDS 보안 그룹 업데이트

RDS 보안 그룹(`rds-aafc-sg`) → 인바운드에 EC2 보안 그룹 ID 추가

### 4-4. Elastic IP 할당 (선택사항)

EC2 → 탄력적 IP → 할당 → EC2에 연결
(인스턴스 재시작해도 IP 유지)

---

## PHASE 5. EC2 서버 환경 구성

### 5-1. EC2 접속

```bash
# Windows PowerShell 또는 WSL
chmod 400 aafc-key.pem
ssh -i aafc-key.pem ubuntu@{EC2_PUBLIC_IP}
```

### 5-2. 시스템 업데이트 및 패키지 설치

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx git
```

### 5-3. 프로젝트 디렉토리 생성 및 코드 배포

```bash
sudo mkdir -p /srv/aafc
sudo chown ubuntu:ubuntu /srv/aafc
cd /srv/aafc
git clone https://github.com/Brad0329/aafc.git .
```

### 5-4. Python 가상환경 및 패키지 설치

```bash
cd /srv/aafc
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5-5. .env 파일 생성

```bash
nano /srv/aafc/.env
```

```ini
DJANGO_SECRET_KEY=실제-시크릿-키-입력
DJANGO_SETTINGS_MODULE=config.settings.prod

DB_NAME=aafc_prod
DB_USER=aafc_user
DB_PASSWORD=RDS-비밀번호
DB_HOST=aafc-db.xxxxxxxxx.ap-northeast-2.rds.amazonaws.com
DB_PORT=5432

AWS_ACCESS_KEY_ID=IAM-액세스-키
AWS_SECRET_ACCESS_KEY=IAM-시크릿-키
AWS_STORAGE_BUCKET_NAME=aafc-media
AWS_S3_REGION_NAME=ap-northeast-2
```

```bash
chmod 600 /srv/aafc/.env  # 소유자만 읽기
```

### 5-6. Django 초기화

```bash
cd /srv/aafc
source venv/bin/activate

# SECRET_KEY 생성 (한 번만 실행)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# DB 마이그레이션
python manage.py migrate --settings=config.settings.prod

# 정적 파일 수집
python manage.py collectstatic --settings=config.settings.prod --noinput

# superuser 생성 (선택)
python manage.py createsuperuser --settings=config.settings.prod
```

---

## PHASE 6. Gunicorn 설정

### 6-1. Gunicorn 동작 테스트

```bash
cd /srv/aafc
source venv/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000
# 브라우저에서 http://{EC2_IP}:8000 접속 확인 후 Ctrl+C
```

### 6-2. Gunicorn systemd 서비스 등록

> ⚠️ workers=2, timeout=120, max-requests=1000 필수 (AWS_SERVICE_STABILITY.md 유형3 참조)

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=AAFC Gunicorn Daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/srv/aafc
EnvironmentFile=/srv/aafc/.env
ExecStart=/srv/aafc/venv/bin/gunicorn \
    --workers 2 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --bind unix:/srv/aafc/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn   # ← EC2 재시작 후 자동 구동 (필수)
sudo systemctl status gunicorn   # active (running) 확인
sudo systemctl is-enabled gunicorn  # "enabled" 출력 확인
```

---

## PHASE 7. Nginx 설정

### 7-1. Nginx 서비스 자동 시작 등록

```bash
sudo systemctl enable nginx  # ← EC2 재시작 후 자동 구동 (필수)
sudo systemctl is-enabled nginx  # "enabled" 출력 확인
```

### 7-3. Nginx 설정 파일 작성

```bash
sudo nano /etc/nginx/sites-available/aafc
```

```nginx
server {
    listen 80;
    server_name {EC2_PUBLIC_IP} www.example.com;  # IP 또는 도메인

    client_max_body_size 50M;  # 파일 업로드 최대 크기

    location = /favicon.ico { access_log off; log_not_found off; }

    # 정적 파일 (collectstatic 결과물)
    location /static/ {
        alias /srv/aafc/staticfiles/;
        expires 30d;
    }

    # Gunicorn 프록시
    location / {
        include proxy_params;
        proxy_pass http://unix:/srv/aafc/gunicorn.sock;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/aafc /etc/nginx/sites-enabled/
sudo nginx -t          # 설정 문법 검사
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 7-2. 방화벽 설정

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## PHASE 8. 데이터 마이그레이션 (로컬 PostgreSQL → RDS)

로컬에서 개발 DB 덤프 → RDS에 복원

```bash
# 로컬 (Windows)
pg_dump -U postgres -d aafc_dev -F c -f aafc_dump.dump

# EC2로 전송
scp -i aafc-key.pem aafc_dump.dump ubuntu@{EC2_IP}:/srv/aafc/

# EC2에서 RDS로 복원
pg_restore -h {RDS_ENDPOINT} -U aafc_user -d aafc_prod -F c aafc_dump.dump
```

> ⚠️ EC2에 postgresql-client 설치 필요: `sudo apt install postgresql-client`

---

## PHASE 9. 최종 확인 및 점검

### 9-0. 서비스 안정성 최종 확인 (AWS_SERVICE_STABILITY.md 전체 체크리스트)

- [ ] 인덱스 추가 마이그레이션 완료 (`python manage.py migrate`)
- [ ] `CONN_MAX_AGE=60` prod.py 설정 확인
- [ ] Gunicorn workers=2, timeout=120, max-requests=1000 확인
- [ ] `sudo systemctl is-enabled gunicorn` → "enabled"
- [ ] `sudo systemctl is-enabled nginx` → "enabled"
- [ ] RDS 스토리지 자동 조정 활성화 확인
- [ ] RDS 백업 시간 새벽 3시 설정 확인
- [ ] CloudWatch 알람 설정 확인

### 9-1. 동작 확인 체크리스트

- [ ] http://{EC2_IP} → 메인 페이지 정상 표시
- [ ] http://{EC2_IP}/accounts/login/ → 로그인 정상
- [ ] http://{EC2_IP}/ba_office/ → 관리자 페이지 정상
- [ ] 미디어 파일 (이미지) 정상 표시 (S3 URL)
- [ ] 정적 파일 (CSS/JS) 정상 로드
- [ ] 파일 업로드 → S3에 저장 확인

### 9-2. 로그 확인

```bash
# Gunicorn 로그
sudo journalctl -u gunicorn -f

# Nginx 접근 로그
sudo tail -f /var/log/nginx/access.log

# Nginx 에러 로그
sudo tail -f /var/log/nginx/error.log
```

### 9-3. 보안 점검

- [ ] DEBUG = False 확인
- [ ] SECRET_KEY 변경 (로컬과 다른 값 사용)
- [ ] .env 파일 권한 600 확인
- [ ] SSH 포트 내 IP만 허용 확인
- [ ] RDS 퍼블릭 액세스 비활성화 확인

---

## PHASE 10. HTTPS 설정 (도메인 있을 경우)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl status certbot.timer  # 자동 갱신 확인
```

settings/prod.py 보안 설정 활성화:
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

---

## 예상 비용 (AWS 프리 티어 기준)

| 서비스 | 사양 | 프리 티어 | 초과 시 월 비용 |
|--------|------|-----------|----------------|
| EC2 | t2.micro | 750시간/월 무료 | ~$9 |
| RDS | db.t3.micro | 750시간/월 무료 | ~$15 |
| S3 | 500MB | 5GB/월 무료 | ~$0.01 |
| 데이터 전송 | - | 15GB/월 무료 | ~$0.09/GB |

> ⚠️ 프리 티어는 계정 생성 후 12개월만 적용

---

## 작업 순서 요약

```
[로컬 코드 작업]
  1. requirements.txt 정리
  2. settings/prod.py 작성
  3. wsgi.py 수정
  4. GitHub push

[AWS 콘솔]
  5. IAM 사용자 생성
  6. S3 버킷 생성 + media 업로드
  7. RDS PostgreSQL 생성
  8. EC2 인스턴스 생성
  9. 보안 그룹 설정 (EC2↔RDS 연결)

[EC2 서버]
  10. 패키지 설치 (Python, Nginx)
  11. git clone + venv + pip install
  12. .env 파일 작성
  13. migrate + collectstatic
  14. Gunicorn systemd 등록
  15. Nginx 설정
  16. 동작 확인

[선택]
  17. 로컬 DB → RDS 데이터 이관
  18. HTTPS (certbot)
```

---

## 참고 파일 경로

| 파일 | 경로 |
|------|------|
| 로컬 settings | `config/settings/local.py` |
| 프로덕션 settings | `config/settings/prod.py` (생성 예정) |
| WSGI | `config/wsgi.py` |
| requirements | `requirements.txt` |
| 환경변수 | `.env` (생성 예정, git 제외) |
