"""자동 SMS/LMS 발송 이벤트 — 원본 ASP 자동발송 재현.

원본은 이벤트 시 인포뱅크 큐(em_smt_tran/em_mmt_tran)에 INSERT → 에이전트 발송.
클라우드(Django)는 각 이벤트에서 인포뱅크 OMNI API를 직접 호출(infobank.send_and_log).

원칙:
  - 모든 함수는 실패해도 예외를 던지지 않는다(자동 알림 실패가 본 트랜잭션/응답을 막지 않도록).
  - 인포뱅크 키 미설정 시 send_and_log 가 테스트(dry-run)로 동작(발송X, 로그만).
  - 발신번호(callback)는 settings.INFOBANK_DEFAULT_CALLBACK (기본 1811-7909).

원본 근거 및 시나리오 매핑: memory/sms-auto-triggers-audit.md
"""
import logging

from django.conf import settings

from . import infobank

logger = logging.getLogger(__name__)

# 무료체험 신청유형 코드 → 명칭 (원본 cfree_new_addproc)
FREE_GBN_NAME = {
    'A1': '신규입단문의',
    'B1': '무료수업체험',
    'C1': '3회체험수업권구입',
    'D1': '기타',
}
# 무료체험 C1(3회권) 주문 링크 (원본 consult_free_proc 하드코딩)
FREE_C1_ORDER_URL = 'https://s.tosspayments.com/BlSiVaJkeWv'


def _notify(to, text, title=None):
    """안전 발송: 수신번호 없으면 skip, 예외는 삼킴(로그만)."""
    to = (to or '').replace('-', '').strip()
    if not to:
        return None
    try:
        return infobank.send_and_log(to, text, settings.INFOBANK_DEFAULT_CALLBACK, title=title)
    except Exception as e:  # 발송 실패가 본 처리를 막지 않게
        logger.warning('자동 SMS 발송 실패(to=%s): %s', to, e)
        return None


# ── 수신자 번호 해석 ─────────────────────────────────────────────
def coach_phone(coach_code):
    """코치코드 → 휴대폰. (원본: lf_coach.mhtel)"""
    from apps.courses.models import Coach
    if not coach_code:
        return ''
    c = Coach.objects.filter(coach_code=coach_code).first()
    return (c.phone if c else '') or ''


def region_manager_phone_by_stadium(sta_code):
    """구장에 배정된 지역담당(coach_level='121') 코치 휴대폰.
    (원본 consult_write_proc: lf_coach+lf_stacoach, coach_level=121, use_gbn='Y')"""
    from apps.courses.models import StadiumCoach
    try:
        sta_code = int(sta_code)
    except (ValueError, TypeError):
        return ''
    sc = StadiumCoach.objects.filter(
        stadium__sta_code=sta_code, coach__use_gbn='Y', coach__coach_level='121'
    ).select_related('coach').first()
    return (sc.coach.phone if sc else '') or ''


def region_manager_phone_by_local(jlocal):
    """지역명 → 상담지역(ConsultRegion) 담당자 휴대폰. (원본 cfree: lf_consult_uplocal)"""
    from apps.consult.models import ConsultRegion
    if not jlocal:
        return ''
    r = ConsultRegion.objects.filter(reg_name=jlocal, del_chk='N').exclude(mphone='').first()
    return (r.mphone if r else '') or ''


def _stadium_name(sta_code):
    from apps.courses.models import Stadium
    try:
        s = Stadium.objects.filter(sta_code=int(sta_code)).first()
    except (ValueError, TypeError):
        s = None
    return (s.sta_name if s else '') or ''


# ── 이벤트 발송 ──────────────────────────────────────────────────
def consult_applied(consult):
    """[5] 프론트 상담신청 → 지역담당자 알림 (원본 consult_write_proc)."""
    to = region_manager_phone_by_stadium(consult.sta_code)
    if not to:
        return
    sta_name = _stadium_name(consult.sta_code)
    text = f'[AAFC] {sta_name} [신청자:{consult.consult_name}]님이 상담 신청하였습니다.'
    _notify(to, text)


def consult_assigned_coach(consult, coach_code):
    """[6][7] 상담 코치배정(답변/등록) → 코치 알림 (원본 consult_reply/input_proc)."""
    to = coach_phone(coach_code)
    if not to:
        return
    text = f'[AAFC][상담관리][신청자:{consult.consult_name}]상담이관되었습니다.'
    _notify(to, text)


def free_applied(free):
    """[9][10] 무료체험 신청 → 지역담당자 알림 (원본 cfree_new_addproc)."""
    to = region_manager_phone_by_local(free.jlocal)
    if not to:
        return
    gbn_nm = FREE_GBN_NAME.get(free.consult_gbn, free.consult_gbn or '')
    text = f'[AAFC] {free.jlocal} [{free.jname}]님이 {gbn_nm} 신청하였습니다.'
    _notify(to, text)


def free_confirmed_c1(free):
    """[8] 무료체험 C1(3회권) 승인 → 신청자에게 주문링크 (원본 consult_free_proc)."""
    if (free.consult_gbn or '') != 'C1':
        return
    to = f'{free.jphone1}{free.jphone2}{free.jphone3}'
    if not to.replace('-', '').strip():
        return
    text = ('[AAFC] 축구체험수업 3회권의 주문 링크를 보내드려요.\n'
            '[링크열기]\n' + FREE_C1_ORDER_URL)
    _notify(to, text)


def payment_completed(member_phone, join_price, lec_price, pay_price,
                      sta_name, lecture_title, period, coach_name, sta_phone):
    """[1][2][4] 결제완료 → 회원 본인 LMS (원본 ex_proc/apply_proc/payment_proc)."""
    if not (member_phone or '').replace('-', '').strip():
        return
    text = (
        '[AAFC]\n'
        '안녕하세요. AAFC입니다.\n'
        '결제내용 안내입니다.\n\n'
        '[포인트 적립]\n'
        '  * 수강료 3개월 납부 시 포인트 1% 적립해드립니다.\n'
        '  * 프로반은 2개월 납부 시 동일 적용\n'
        '  * 기한 = 해당월 말일까지 결제한 회원에게 포인트 지급\n'
        '[결제정보]\n'
        f'  * 교육용품비 = {join_price:,}원\n'
        f'  * 수강료 = {lec_price:,}원\n'
        f'  * 총 결제금액 = {pay_price:,}원\n\n'
        '[수업정보]\n'
        f'  * 구장 = {sta_name}\n'
        f'  * 클래스 = {lecture_title}\n'
        f'  * 수강월 = {period}\n'
        f'  * 담당 코치 = {coach_name}\n'
        f'  * 야드 연락처 = {sta_phone}'
    )
    _notify(member_phone, text, title='수강료결제 안내')


def new_enrollment_coach(coach_code, sta_name, lecture_title, child_name):
    """[3] 신규입단 완료 → 담당코치 알림 (원본 apply_proc)."""
    to = coach_phone(coach_code)
    if not to:
        return
    text = f'[AAFC][{sta_name}][{lecture_title}][{child_name}]신규입단 하였습니다.'
    _notify(to, text)
