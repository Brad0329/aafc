"""인포뱅크(InfoBank) OMNI API — SMS/LMS/MMS 발송 클라이언트.

원본 ASP는 InfoBank 'DB연동' 방식이었다: 웹은 MSSQL `em_smt_tran`/`em_mmt_tran`
큐 테이블에 INSERT 만 하고, InfoBank 에이전트가 그 테이블을 폴링해 실제 발송했다.
클라우드(Django/RDS)에는 그 에이전트가 없으므로 InfoBank OMNI REST API(HTTPS)로
직접 호출한다.

흐름:
  1. get_token() : 헤더 X-IB-Client-Id / X-IB-Client-Passwd 로 access token 발급
                   (Bearer, 만료시각 포함) → 만료 전까지 캐시
  2. send()      : Authorization: Bearer {token} 로 /send/omni 호출
                   - SMS(≤90byte)   : messageFlow[].sms{from,text}
                   - LMS(>90byte)   : messageFlow[].mms{from,title,text}
                   - MMS(이미지첨부) : messageFlow[].mms{..., fileKey:[...]}

문서: https://infobank-guide.gitbook.io/omni_api/  (OMNI API v1)
엔드포인트: 인증 https://omni.ibapi.kr/v1/auth/token, 발송 https://mars.ibapi.kr/api/comm/v1/send/omni

※ 실제 계정/상품에 따라 엔드포인트·인증헤더·응답필드가 다를 수 있다. 모두 settings 로
  조정 가능하게 두었으며, API 키 확보 후 1건 실발송으로 응답코드(A000=성공)·msgKey 를
  반드시 확인할 것. 자격증명 미설정 시에는 send_and_log() 가 테스트(dry-run)로 동작한다.
"""
import logging

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

TIMEOUT = 10
_TOKEN_CACHE_KEY = 'infobank_omni_token'
_SCHEMA_CACHE_KEY = 'infobank_omni_schema'
SUCCESS_CODE = 'A000'


def sms_byte_len(text):
    """SMS 표준 바이트 길이 — 비ASCII(한글 등)=2byte. 90byte 이하 SMS, 초과 LMS."""
    return sum(2 if ord(ch) > 0x7F else 1 for ch in (text or ''))


def pick_service_type(text, title=None, file_keys=None):
    """SMSLog.service_type 코드: '0'=SMS, '3'=LMS, '2'=MMS(이미지)."""
    if file_keys:
        return '2'
    if title or sms_byte_len(text) > 90:
        return '3'
    return '0'


def is_configured():
    """인포뱅크 자격증명 설정 여부. 미설정이면 테스트(dry-run) 모드.

    통합 KEY(V2) 또는 옴니 계정 ID/PW(V1) 둘 중 하나만 있으면 설정된 것으로 본다.
    """
    if getattr(settings, 'INFOBANK_API_KEY', ''):
        return True
    return bool(settings.INFOBANK_CLIENT_ID and settings.INFOBANK_CLIENT_PASSWD)


def _get_auth():
    """발송에 쓸 (schema, credential) 반환. 실패 시 None.

    반환값은 Authorization 헤더에 그대로 넣을 값(문자열).
    - 통합 KEY(V2): 접두어 없이 키 그대로. (`Authorization: {키}` — Bearer 붙이면 A401 AUTH_FAILED)
    - 옴니 계정(V1): `{schema} {token}` (보통 `Bearer {token}`).
    """
    api_key = getattr(settings, 'INFOBANK_API_KEY', '')
    if api_key:
        return api_key
    token = get_token()
    if not token:
        return None
    return f"{cache.get(_SCHEMA_CACHE_KEY, 'Bearer')} {token}"


def get_token():
    """access token 발급(+캐시). 실패 시 None."""
    token = cache.get(_TOKEN_CACHE_KEY)
    if token:
        return token
    try:
        resp = requests.post(
            settings.INFOBANK_AUTH_URL,
            headers={
                'X-IB-Client-Id': settings.INFOBANK_CLIENT_ID,
                'X-IB-Client-Passwd': settings.INFOBANK_CLIENT_PASSWD,
                'Content-Type': 'application/json',
            },
            timeout=TIMEOUT,
        )
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning('인포뱅크 토큰 발급 실패: %s', e)
        return None
    # 응답 래핑(data.xxx) 여부 + 필드명(token/accessToken) 양쪽 대응
    body = data.get('data', data) if isinstance(data, dict) else {}
    token = (body.get('token') or body.get('accessToken')
             or data.get('token') or data.get('accessToken'))
    # 인증 schema(Bearer/Basic 등)는 응답값을 따르되 없으면 Bearer
    schema = body.get('schema') or data.get('schema') or 'Bearer'
    if not token:
        logger.error('인포뱅크 토큰 응답에 token/accessToken 없음: %s', data)
        return None
    # 만료 60초 전까지 캐시(파싱 실패 시 보수적으로 30분)
    ttl = 1800
    expired = body.get('expired') or data.get('expired')
    if expired:
        try:
            exp_dt = timezone.datetime.fromisoformat(expired)
            ttl = max(60, int((exp_dt - timezone.now()).total_seconds()) - 60)
        except (ValueError, TypeError):
            pass
    cache.set(_TOKEN_CACHE_KEY, token, ttl)
    cache.set(_SCHEMA_CACHE_KEY, schema, ttl)
    return token


def send(to, text, callback, title=None, file_keys=None):
    """단건 발송(실호출). 반환 dict(ok, code, result, msg_key, service_type, raw)."""
    to = (to or '').replace('-', '').strip()
    callback = (callback or '').replace('-', '').strip()
    service_type = pick_service_type(text, title, file_keys)

    if service_type == '0':
        flow = {'sms': {'from': callback, 'text': text}}
    else:
        mms = {'from': callback, 'title': (title or text)[:40], 'text': text}
        if file_keys:
            mms['fileKey'] = file_keys
        flow = {'mms': mms}
    payload = {'messageFlow': [flow], 'destinations': [{'to': to}]}

    auth = _get_auth()
    if not auth:
        return {'ok': False, 'code': 'AUTH', 'result': '인증 실패(토큰/통합키)',
                'msg_key': '', 'service_type': service_type, 'raw': None}

    try:
        resp = requests.post(
            settings.INFOBANK_SEND_URL,
            headers={'Authorization': auth, 'Content-Type': 'application/json'},
            json=payload, timeout=TIMEOUT,
        )
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning('인포뱅크 발송 실패: %s', e)
        return {'ok': False, 'code': 'HTTP', 'result': str(e),
                'msg_key': '', 'service_type': service_type, 'raw': None}

    # 응답 envelope: {"common":{"authCode","authResult",...}, "data":{"destinations":[{"msgKey",...}]}}
    # (인증/ACL 오류도 common.authCode 로 전달됨: A000 성공 / A401 인증실패 / A403 ACL 등)
    body = data if isinstance(data, dict) else {}
    common = body.get('common') if isinstance(body.get('common'), dict) else {}
    code = common.get('authCode') or body.get('code', '')
    result = common.get('authResult') or body.get('result', '')
    msg_key = ''
    inner = body.get('data') if isinstance(body.get('data'), dict) else None
    dests = inner.get('destinations') if inner else body.get('destinations')
    if isinstance(dests, list) and dests:
        msg_key = dests[0].get('msgKey', '')
        code = dests[0].get('code', code) or code
        result = dests[0].get('result', result) or result
    return {'ok': code == SUCCESS_CODE, 'code': code, 'result': result,
            'msg_key': msg_key, 'service_type': service_type, 'raw': data}


def send_and_log(to, text, callback, title=None, file_keys=None, broadcast=False):
    """발송 + SMSLog 이력 기록. 자격증명 미설정 시 테스트(dry-run): 실발송 없이 이력만.

    반환 dict(ok, test, code, result, msg_key).
    """
    from .models import SMSLog  # 순환참조 방지(지연 import)

    service_type = pick_service_type(text, title, file_keys)
    log = SMSLog(
        date_client_req=timezone.now(),
        subject=(title or '')[:40],
        content=text,
        callback=(callback or '').replace('-', ''),
        service_type=service_type,
        recipient_num=(to or '').replace('-', ''),
        broadcast_yn='Y' if broadcast else 'N',
    )

    if not is_configured():
        # 테스트(dry-run) 모드 — 실제 발송 없이 이력만 'T'로 남김
        log.msg_status = 'T'
        log.rslt = 'TEST'
        log.save()
        return {'ok': True, 'test': True, 'code': 'TEST',
                'result': '테스트모드(실제 발송 안 함)', 'msg_key': ''}

    res = send(to, text, callback, title=title, file_keys=file_keys)
    log.msg_status = '1' if res['ok'] else 'F'
    log.msg_key = (res.get('msg_key') or '')[:20]
    log.rslt = (res.get('code') or '')[:10]
    if res['ok']:
        log.date_sent = timezone.now()
    log.save()
    res['test'] = False
    return res
