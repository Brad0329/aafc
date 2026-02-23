# AAFC Django AWS 배포 가이드

> 작성일: 2026-02-23
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

## 코드 업데이트 절차 (로컬 변경 후 EC2 반영)

```bash
# 1. 로컬에서 코드 수정 후 GitHub push
git add .
git commit -m "변경 내용"
git push origin main

# 2. EC2에서 pull 및 재시작
cd /srv/aafc && git pull && sudo systemctl restart gunicorn
```

> 정적파일 변경 시 collectstatic 추가 실행:
> ```bash
> source venv/bin/activate && python manage.py collectstatic --noinput && sudo systemctl restart gunicorn
> ```

---

## 서비스 관리 명령어

```bash
# Gunicorn 상태 확인
sudo systemctl status gunicorn

# Gunicorn 재시작
sudo systemctl restart gunicorn

# Nginx 재시작
sudo systemctl restart nginx

# 로그 확인
sudo journalctl -u gunicorn -n 50 --no-pager
sudo tail -f /var/log/nginx/error.log
```

---

## 미디어 파일 S3 업로드 (신규 추가 시)

```powershell
# 로컬 PowerShell
aws s3 sync "C:\Users\user\Documents\aafc\media" s3://aafc-bucket/ --region ap-northeast-2
```

---

## DB 데이터 이관 (로컬 → RDS)

```powershell
# 1. 로컬에서 dump 생성
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -U postgres -d aafc_dev -F c -f C:\Users\user\Downloads\aafc_dump.dump

# 2. EC2로 전송
scp -i "C:\Users\user\Downloads\aafc-key.pem" "C:\Users\user\Downloads\aafc_dump.dump" ubuntu@43.201.113.91:/srv/aafc/
```

```bash
# 3. EC2에서 RDS로 복원
pg_restore -h aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com -U aafc_user -d aafc_prod -F c --clean --if-exists /srv/aafc/aafc_dump.dump
```

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

## 접속 URL

| 항목 | URL |
|------|-----|
| 메인 사이트 | http://43.201.113.91 |
| 관리자 페이지 | http://43.201.113.91/ba_office/ |
| 관리자 계정 | junior2019 / test1234 |
