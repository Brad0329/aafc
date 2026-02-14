def office_user(request):
    """관리자 세션 정보를 템플릿 컨텍스트로 전달"""
    return {
        'office_user': request.session.get('office_user'),
    }
