#!/bin/bash
# AAFC 운영 EC2 배포 스크립트
# 사용: bash scripts/deploy.sh   (또는 Claude Code에서 /deploy)
# 동작: EC2 SSH → git pull → pip → migrate → collectstatic → gunicorn restart
#
# ⚠️ commit/push 만으론 운영에 반영되지 않음. push 후 이 스크립트로 배포해야 함.
set -e

KEY="C:/Users/user/Downloads/aafc-key.pem"
HOST="ubuntu@3.34.153.141"
APP="/srv/aafc"

echo "===== AAFC EC2 배포 시작 ($HOST) ====="
ssh -i "$KEY" -o ConnectTimeout=25 "$HOST" "cd $APP && \
  echo '-- git pull --'      && git pull origin main 2>&1 | tail -6 && \
  source venv/bin/activate && \
  echo '-- pip --'           && pip install -r requirements.txt -q 2>&1 | tail -1 && \
  echo '-- migrate --'       && python manage.py migrate --settings=config.settings.prod 2>&1 | tail -6 && \
  echo '-- collectstatic --' && python manage.py collectstatic --noinput --settings=config.settings.prod 2>&1 | tail -1 && \
  echo '-- restart --'       && sudo systemctl restart gunicorn && sleep 2 && \
  (systemctl is-active gunicorn && echo '✅ DEPLOY_OK (gunicorn active)' \
     || (echo '❌ gunicorn 시작 실패 — 로그:' && sudo journalctl -u gunicorn -n 20 --no-pager))"
echo "===== 배포 종료 ====="
