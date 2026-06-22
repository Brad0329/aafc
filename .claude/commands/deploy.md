---
description: 운영 EC2에 최신 코드 배포 (git pull + migrate + collectstatic + gunicorn restart)
---

운영 EC2(`3.34.153.141`, `/srv/aafc`)에 origin/main 최신 코드를 배포한다.

`bash scripts/deploy.sh` 를 Bash로 실행하고, 출력에서 다음을 확인해 사용자에게 간결히 보고한다:
- git pull로 받아온 변경(파일 수 / 주요 파일)
- migrate 적용 여부 (모델 변경이 있었는지)
- 마지막에 `DEPLOY_OK (gunicorn active)` 가 떴는지

gunicorn이 실패(journalctl 로그 출력)하면 원인을 진단한다. **흔한 원인**: 새 코드가 요구하는 `.env` 키(예: `NICE_*`, `TOSS_*`)가 EC2에 없어 settings 로드 실패 → 해당 키를 EC2 `/srv/aafc/.env`에 추가해야 함.

참고:
- 배포는 origin/main을 받아오므로, 로컬 변경이 아직 push 안 됐으면 **먼저 commit + push**가 필요하다.
- 배포 후 핵심 동작(홈 200 등)을 확인하려면 `curl -s -o /dev/null -w "%{http_code}" http://3.34.153.141/` 로 점검한다.
