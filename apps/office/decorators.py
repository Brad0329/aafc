from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def office_login_required(view_func):
    """관리자 로그인 체크 데코레이터"""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('office_user'):
            return redirect('office_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


def office_permission_required(permission_code):
    """관리자 메뉴 권한 체크 데코레이터
    permission_code: A=시스템, M=회원, C=상담, H=수강생, L=과정, N=출고, R=REPORT, P=포탈, S=쇼핑몰
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            office_user = request.session.get('office_user')
            if not office_user:
                return redirect('office_login')
            power_level = office_user.get('power_level', '')
            if permission_code not in power_level:
                return HttpResponseForbidden('해당 메뉴에 대한 접근 권한이 없습니다.')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
