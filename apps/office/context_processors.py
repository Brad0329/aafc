from django.conf import settings


def office_user(request):
    """관리자 세션 정보를 템플릿 컨텍스트로 전달"""
    ou = request.session.get('office_user')
    # [원본 ASP 재현] 수강확정/결제완료 옵션 노출 권한 (power_id 화이트리스트)
    # ※ 임시 하드코딩 — 오픈 후 OfficeUser 권한 플래그로 리팩터링 예정(백로그)
    office_can_confirm = bool(
        ou and ou.get('office_id') in settings.STUDENT_CONFIRM_ALLOWED_IDS
    )
    return {
        'office_user': ou,
        'office_can_confirm': office_can_confirm,
    }
