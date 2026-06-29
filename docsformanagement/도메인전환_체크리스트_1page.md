# AAFC 도메인 전환 D-day 체크리스트 (1page)

> 케이스: **기존 도메인 aafc.co.kr 그대로** ASP → Django(EC2)로 이전 + **Toss 결제**
> 상세: `도메인전환_시나리오.md` / 역할: **[운영자]=직접 수행**, 그 외=개발/함께

---

## ⚠ 사전 준비 (D-1 ~ D-2 완료)
□ **[운영자]** aafc.co.kr DNS 관리 계정 로그인 확인 (가비아/후이즈 등) + **TTL 300초(5분)로 낮춤**
□ **[운영자]** Toss 개발자센터 → 내 상점 → **aafc.co.kr 도메인 등록** (live 결제 허용)
□ **[운영자]** 기존 MSSQL 최신 `.bak` 받을 경로/담당 확인 (D-day에 최신본 확보)
□ HTTPS 인증서 **DNS-01 사전 발급** (DNS 전환 전 미리 — 다운타임 최소화)
  `sudo certbot certonly --manual --preferred-challenges dns -d aafc.co.kr -d www.aafc.co.kr`
  (등록업체에 TXT 레코드 추가 → 검증) ※ 못 하면 당일 DNS 전환 후 `--nginx`로 발급
□ RDS 자동백업 + 수동 dump 1개  □ 마이그레이션 14개 로컬 dry-run 완료
□ EC2 nginx에 aafc.co.kr server block 미리 작성 (인증서 경로 포함, reload는 당일)

---

## D-day 타임라인

| 시간 | 작업 | 명령/파일 |
|------|------|-----------|
| **09:00** | □ **[운영자]** 기존 사이트 점검공지 + **가입/결제 차단** | 기존 ASP 관리자 |
| **09:10** | □ RDS 현재상태 dump (롤백용) | `pg_dump … -f aafc_rds_backup_before_cutover.dump` |
| **09:20** | □ **[운영자]** 기존 MSSQL **최신 `.bak` 확보** → 로컬 복원 | `sqlcmd … RESTORE DATABASE` |
| **09:30** | □ 로컬 PG 초기화 + Django migrate | `DROP SCHEMA public CASCADE…` / `migrate` |
| **09:35** | □ migrate_*.py 14개 일괄 실행 | common→members→courses→course_src→enrollment→board→consult→shop→points→notifications→reports→training→office→popup |
| **09:55** | □ **이관 검증** — 🔴 0개 + 금액 ✅ + **프로모션회원 0건 아님** 확인 후 진행 (NG면 중단·재이관) | `python scripts/verify_migration.py` |
| **10:00** | □ 로컬 PG → dump 생성 | `pg_dump -U postgres -d aafc_dev -F c -f aafc_dump_YYYYMMDD.dump` |
| **10:05** | □ scp로 EC2 전송 | `scp -i aafc-key.pem … ubuntu@3.34.153.141:/srv/aafc/aafc_dump.dump` |
| **10:10** | □ RDS pg_restore | `pg_restore … --clean --if-exists --no-owner /srv/aafc/aafc_dump.dump` |
| **10:20** | □ EC2 코드 최신화 | `git pull` / `pip install -r requirements.txt` / `migrate` / `collectstatic --noinput` |
| **10:30** | □ `.env` 수정: ALLOWED_HOSTS=aafc.co.kr,www.aafc.co.kr + **Toss live 키** | `sudo nano /srv/aafc/.env` (아래 명령) |
| **10:40** | □ prod.py SSL 주석 해제 확인 (push돼 있으면 자동) | SECURE_SSL_REDIRECT 등 |
| **10:45** | □ nginx aafc.co.kr block reload (인증서 사전발급분 적용) | `sudo nginx -t && sudo systemctl reload nginx` |
| **10:50** | □ **[운영자]** **DNS A레코드 변경**: aafc.co.kr / www → **3.34.153.141** | DNS 관리 콘솔 |
| **11:00** | □ (사전발급 못했으면) certbot 발급 | `sudo certbot --nginx -d aafc.co.kr -d www.aafc.co.kr` |
| **11:05** | □ Gunicorn 재시작 + 전파 대기 | `sudo systemctl restart gunicorn` |
| **11:10** | □ 검증 (다음 박스) | |
| **12:00** | □ **[운영자]** 정상화 공지 | 홈배너 + SMS |

---

## 11:10 검증 체크리스트
□ `https://aafc.co.kr` 메인 로드 + 자물쇠(인증서) 정상
□ 로그인 (기존 회원 SHA256 호환)
□ 수강신청 1건 + **Toss 100원 실결제** → Toss 개발자센터에서 확인 후 취소
□ 쇼핑몰 주문 1건 + **Toss 100원 실결제** → 취소
□ 게시판 글 작성 + 파일 업로드
□ `/ba_office/` 사무실 IP에서 접속
□ 알림장/SMS 발송 1건  □ S3 이미지 정상 로드  □ CloudWatch 알람 정상

---

## 🚨 롤백 (핵심기능 30분 내 복구 불가 시)
| 빠름 | DNS 원복 | aafc.co.kr A레코드를 **기존 ASP 서버 IP로 되돌림** (TTL 5분이라 빠름) + 기존 사이트 차단 해제 |
| 데이터 | RDS 복원 | `pg_restore … aafc_rds_backup_before_cutover.dump` + `restart gunicorn` |

> 같은 도메인이라 redirect 불필요 — 롤백은 **DNS를 기존 서버로 되돌리기**가 전부.

---

## 핵심 명령 (복붙)

**EC2 SSH** `ssh -i "C:\Users\user\Downloads\aafc-key.pem" ubuntu@3.34.153.141`

**.env Toss live 키 적용** (※ 시크릿키 끝 콜론 `:` 제거!)
```
# ⚠️ live 키 실제 값은 Toss 개발자센터 / 비밀번호 관리자에서 가져올 것 (문서에 평문 보관 금지)
sudo sed -i 's|^TOSS_CLIENT_KEY=.*|TOSS_CLIENT_KEY=<live 클라이언트 키>|' /srv/aafc/.env
sudo sed -i 's|^TOSS_SECRET_KEY=.*|TOSS_SECRET_KEY=<live 시크릿 키 · 끝 콜론 제거>|' /srv/aafc/.env
sudo systemctl restart gunicorn
```

**RDS 복원** `PGPASSWORD='****' pg_restore -h aafc-db.cdaqmq8yqnjw.ap-northeast-2.rds.amazonaws.com -U aafc_user -d aafc_prod -F c --clean --if-exists --no-owner /srv/aafc/aafc_dump.dump`

**서비스/로그** `sudo systemctl restart gunicorn && sudo systemctl reload nginx` / `sudo journalctl -u gunicorn -n 100 --no-pager`

---

## 비상 연락처 (☎ 사전 기입)
| 항목 | 연락처 |
|------|--------|
| AWS 콘솔 (pesseq@gmail.com) | https://console.aws.amazon.com |
| 도메인 등록업체 (aafc.co.kr DNS) | ☎ ______________ |
| Toss 결제 고객센터 | 1544-7772 / 개발자센터 docs.tosspayments.com |
| 기존 ASP 서버 관리자 | ☎ ______________ |
| AAFC 운영 담당자 | ☎ ______________ |
| SMS 발송 업체 (KYT) | ☎ ______________ |

---

## 참고: NICE 본인인증
- 현재 **미연동(Phase 9 보류)**. 회원가입에 본인인증 없음 → 전환 체크 대상 아님. 추후 연동 시 NICE 가맹점에 aafc.co.kr 등록 별도 진행.
