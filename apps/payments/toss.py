"""Toss Payments 공용 유틸 (수강신청/쇼핑몰 공유).

수강신청(apps.payments)과 쇼핑몰(apps.shop)이 함께 사용한다.
결제 승인/취소 API 호출, 결제수단 코드 매핑, 결제 로그 공통 필드 빌더.
"""
import json

import requests
from django.conf import settings

CONFIRM_URL = 'https://api.tosspayments.com/v1/payments/confirm'

# Toss 결제수단명 → (pay_method, use_pay_method 12자리 코드)
TOSS_METHOD_CODES = {
    '카드': ('CARD', '100000000000'),
    '계좌이체': ('R', '010000000000'),
    '가상계좌': ('VACCT', '001000000000'),
}


def method_to_codes(method):
    """결제수단명 → (pay_method, use_pay_method). 미지정/미지원은 카드로."""
    return TOSS_METHOD_CODES.get(method, ('CARD', '100000000000'))


def _post(url, payload):
    """Toss API POST 공통 (Basic 인증 = base64('secretKey:')). → (http_code, json)"""
    try:
        resp = requests.post(
            url,
            json=payload,
            auth=(settings.TOSS_SECRET_KEY, ''),
            headers={'Content-Type': 'application/json'},
            timeout=30,
        )
        try:
            body = resp.json()
        except ValueError:
            body = {}
        return resp.status_code, body
    except requests.RequestException as e:
        return 0, {'code': 'NETWORK_ERROR', 'message': str(e)}


def confirm(payment_key, order_id, amount):
    """결제 승인 → (http_code, json). http_code==200 이고 status=='DONE' 이면 승인 완료."""
    return _post(getattr(settings, 'TOSS_CONFIRM_URL', CONFIRM_URL), {
        'paymentKey': payment_key,
        'orderId': order_id,
        'amount': int(amount),
    })


def cancel(payment_key, reason):
    """결제 전액 취소 → (http_code, json). 승인 후 후처리 실패 시 보상 취소용."""
    url = f'https://api.tosspayments.com/v1/payments/{payment_key}/cancel'
    return _post(url, {'cancelReason': reason})


def build_log_kwargs(confirm_json, http_code, use_pay_method):
    """PaymentToss/ShopPaymentToss 공통 필드 kwargs (모델별 고유 필드는 호출측에서 추가)."""
    card = confirm_json.get('card') or {}
    transfer = confirm_json.get('transfer') or {}
    return {
        'payment_key': confirm_json.get('paymentKey', ''),
        'amount': int(confirm_json.get('totalAmount', 0) or 0),
        'method': confirm_json.get('method', ''),
        'status': confirm_json.get('status', ''),
        'use_pay_method': use_pay_method,
        'http_code': http_code,
        'res_cd': confirm_json.get('code', ''),
        'res_msg': confirm_json.get('message', ''),
        'card_name': card.get('company', ''),
        'card_no': card.get('number', ''),
        'app_no': card.get('approveNo', ''),
        'quota': str(card.get('installmentPlanMonths', '') or ''),
        'noinf': 'Y' if card.get('isInterestFree') else 'N',
        'bank_name': transfer.get('bank', ''),
        'bank_code': transfer.get('bankCode', ''),
        'approved_at': confirm_json.get('approvedAt', ''),
        'raw_response': json.dumps(confirm_json, ensure_ascii=False),
    }
