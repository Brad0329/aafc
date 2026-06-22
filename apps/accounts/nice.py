"""NICE 통합인증 API 연동 (회원가입 휴대폰 본인확인).

ASP 구버전(CPClient.Kisinfo COM, CheckPlus Safe)을 대체하는 NICE 통합인증 API.
구버전은 Windows COM 컴포넌트라 Django(Python)에서 사용 불가 → 통합인증 API(신버전)로 재구현.

흐름:
  1. get_access_token()  : access_token / ticket / iterators 발급
  2. request_auth_url()  : 인증창 URL + transaction_id 발급 (휴대폰 svc_types=['M'])
  3. (사용자가 표준창에서 본인인증) → return_url 로 web_transaction_id 수신
  4. request_result()    : enc_data / integrity_value 조회
  5. decrypt_result()    : PBKDF2 키유도 → AES-256-GCM 복호화 (이름/생년월일/성별/DI/CI/휴대폰)

참고: https://auth-guide.niceid.co.kr/

주의(실제 키로 end-to-end 테스트 시 확인 필요):
  - 응답 래핑 구조(dataHeader/dataBody) 여부 → body.get('dataBody', body) 로 양쪽 대응
  - integrity_value HMAC 대상/인코딩(enc_data 문자열 기준 base64url)
"""
import base64
import hashlib
import hmac
import json
import logging
import secrets

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = 30


def _b64url_nopad(raw: bytes) -> str:
    """Base64 URL-safe 인코딩 (패딩 제거) — NICE 규격."""
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def _b64url_decode(s: str) -> bytes:
    """Base64 URL-safe 디코딩 (패딩 보정)."""
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def gen_request_no() -> str:
    """요청 고유번호 (영숫자 20~50 byte). 'A' + 32 hex = 33자."""
    return 'A' + secrets.token_hex(16)


def _api_base() -> str:
    return settings.NICE_API_BASE.rstrip('/')


def _post(path, payload, headers):
    """공통 POST → (ok, dataBody dict). 실패 시 (False, {})."""
    try:
        resp = requests.post(
            f'{_api_base()}{path}', json=payload,
            headers={**headers, 'Content-Type': 'application/json'},
            timeout=TIMEOUT,
        )
        body = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning('NICE %s 호출 실패: %s', path, e)
        return False, {}
    # NICE 응답은 dataHeader/dataBody 로 감싸는 경우가 있어 양쪽 대응
    return True, body.get('dataBody', body)


def get_access_token():
    """1단계: access_token 발급.

    Authorization: Basic base64url(client_id:client_secret)
    반환: dict(access_token, ticket, iterators, ...) 또는 None
    """
    cid, secret = settings.NICE_CLIENT_ID, settings.NICE_CLIENT_SECRET
    if not cid or not secret:
        logger.error('NICE_CLIENT_ID/SECRET 미설정 — .env 확인 필요')
        return None
    basic = _b64url_nopad(f'{cid}:{secret}'.encode())
    ok, data = _post(
        '/auth/token',
        {'grant_type': 'client_credentials', 'request_no': gen_request_no()},
        {'Authorization': f'Basic {basic}'},
    )
    if not ok or not data.get('access_token'):
        return None
    return data


def request_auth_url(access_token, return_url=None):
    """2단계: 인증창 URL 발급 (휴대폰 본인확인).

    반환: dict(auth_url, transaction_id, request_no) 또는 None
    """
    req_no = gen_request_no()
    ok, data = _post(
        '/auth/url',
        {
            'request_no': req_no,
            'return_url': return_url or settings.NICE_RETURN_URL,
            'svc_types': ['M'],      # M: 휴대폰 본인확인
            'method_type': 'POST',   # 콜백 전송 방식
        },
        {'Authorization': f'Bearer {access_token}'},
    )
    if not ok or not data.get('auth_url'):
        return None
    data.setdefault('request_no', req_no)
    return data


def request_result(access_token, web_transaction_id, transaction_id, request_no):
    """4단계: 인증 결과 조회.

    반환: dict(enc_data, integrity_value, ...) 또는 None
    """
    ok, data = _post(
        '/auth/result',
        {
            'web_transaction_id': web_transaction_id,
            'transaction_id': transaction_id,
            'request_no': request_no,
        },
        {'Authorization': f'Bearer {access_token}'},
    )
    if not ok or not data.get('enc_data'):
        return None
    return data


def decrypt_result(enc_data, integrity_value, ticket, transaction_id, iterators):
    """5단계: enc_data 복호화 + 무결성 검증.

    - keyString = base64url_nopad(PBKDF2-HMAC-SHA256(ticket, salt=transaction_id, iters, 64byte))
    - AES키 = keyString[0:32], HMAC키 = keyString[48:80]
    - enc_data(base64url) = IV(16) + ciphertext + Tag(16), AES-256-GCM
    반환: dict(name, birthdate, gender, di, ci, mobileno, ...) 또는 None
    """
    try:
        dk = hashlib.pbkdf2_hmac(
            'sha256', ticket.encode(), transaction_id.encode(), int(iterators), dklen=64,
        )
        key_string = _b64url_nopad(dk)
        aes_key = key_string[0:32].encode()
        hmac_key = key_string[48:80].encode()

        # 무결성 검증 (integrity_value = base64url(HMAC-SHA256(enc_data 문자열)))
        if integrity_value:
            calc = _b64url_nopad(hmac.new(hmac_key, enc_data.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(calc, integrity_value):
                logger.error('NICE 무결성 검증 실패')
                return None

        raw = _b64url_decode(enc_data)
        iv, ct_and_tag = raw[:16], raw[16:]   # AESGCM 은 마지막 16byte 를 tag 로 처리
        plain = AESGCM(aes_key).decrypt(iv, ct_and_tag, None)
        return json.loads(plain.decode('utf-8'))
    except Exception:
        logger.exception('NICE 결과 복호화 실패')
        return None
