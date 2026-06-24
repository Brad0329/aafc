import re
import secrets
import string
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from . import nice
from .forms import LoginForm, RegisterForm, ProfileForm, MemberChildForm, CustomPasswordChangeForm
from .models import Member, MemberChild


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


def _is_under_14(birth_yyyymmdd):
    """birth(YYYYMMDD) 기준 만 14세 미만 여부 (ASP join_01 동일 차단)."""
    try:
        y, m, d = int(birth_yyyymmdd[:4]), int(birth_yyyymmdd[4:6]), int(birth_yyyymmdd[6:8])
        today = date.today()
        age = today.year - y - ((today.month, today.day) < (m, d))
        return age < 14
    except (ValueError, IndexError):
        return False


def register_view(request):
    """회원가입 1단계 — 약관 동의 + 휴대폰 본인인증 (ASP join_01.asp).
    인증 성공 시 콜백이 부모창을 step2로 이동시킨다."""
    return render(request, 'accounts/register.html')


USERID_RE = re.compile(r'^[a-z0-9]{6,16}$')


def _id_exists(uid):
    """아이디 중복 — 회원/자녀/관리자 전체 (ASP join_write_proc 동일)."""
    from apps.office.models import OfficeUser
    return (Member.objects.filter(username=uid).exists()
            or MemberChild.objects.filter(child_id=uid).exists()
            or OfficeUser.objects.filter(office_id=uid).exists())


def ajax_id_check(request):
    """아이디 중복확인 AJAX (ASP member_idchk_proc.asp)."""
    uid = request.GET.get('id', '').strip()
    available = bool(USERID_RE.match(uid)) and not _id_exists(uid)
    return JsonResponse({'available': available})


def register_step2_view(request):
    """회원가입 2단계 — 정보입력 + 가입 (ASP join_02.asp / join_write_proc.asp)."""
    nice_auth = request.session.get('nice_auth')
    if not nice_auth or not nice_auth.get('verified'):
        messages.error(request, '휴대폰 본인인증을 먼저 진행해주세요.')
        return redirect('accounts:register')

    if request.method == 'POST':
        # 만 14세 미만 / DI 중복가입 차단
        if _is_under_14(nice_auth.get('birth', '')):
            request.session.pop('nice_auth', None)
            messages.error(request, '만 14세 미만은 가입할 수 없습니다.')
            return redirect('accounts:register')
        di = nice_auth.get('di', '')
        if di and Member.objects.filter(join_safe_di=di, status='N').exists():
            request.session.pop('nice_auth', None)
            messages.error(request, '이미 가입된 사용자입니다.')
            return redirect('accounts:register')

        username = request.POST.get('username', '').strip()
        pwd1 = request.POST.get('password1', '')
        pwd2 = request.POST.get('password2', '')
        phone = '-'.join(p for p in [request.POST.get('mhtel1', ''),
                                     request.POST.get('mhtel2', '').strip(),
                                     request.POST.get('mhtel3', '').strip()] if p)
        mail1 = request.POST.get('member_mail1', '').strip()
        mail2 = request.POST.get('member_mail2', '').strip()
        email = f'{mail1}@{mail2}' if mail1 and mail2 else ''
        zipcode = request.POST.get('zipcode', '').strip()
        address1 = request.POST.get('address1', '').strip()
        address2 = request.POST.get('address2', '').strip()
        ctx = {'nice_auth': nice_auth, 'post': request.POST}

        if not USERID_RE.match(username):
            messages.error(request, '아이디는 영문 소문자·숫자 6~16자로 입력하세요.')
            return render(request, 'accounts/register_step2.html', ctx)
        if _id_exists(username):
            messages.error(request, f'{username} 은(는) 이미 사용중인 아이디입니다.')
            return render(request, 'accounts/register_step2.html', ctx)
        if not pwd1 or pwd1 != pwd2:
            messages.error(request, '비밀번호를 확인하여 주세요.')
            return render(request, 'accounts/register_step2.html', ctx)
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]{8,}$', pwd1):
            messages.error(request, '비밀번호는 영문·숫자 조합 8자 이상이어야 합니다.')
            return render(request, 'accounts/register_step2.html', ctx)
        if username == pwd1:
            messages.error(request, '아이디와 비밀번호를 같게 사용할 수 없습니다.')
            return render(request, 'accounts/register_step2.html', ctx)
        if not phone or not email or not (zipcode and address1 and address2):
            messages.error(request, '필수정보가 부족합니다.')
            return render(request, 'accounts/register_step2.html', ctx)

        # 가입 (신원정보는 본인인증 세션값으로 확정 — 위변조 방지)
        user = Member(
            username=username, name=nice_auth.get('name', ''),
            phone=phone, email=email, zipcode=zipcode,
            address1=address1, address2=address2,
            birth=nice_auth.get('birth', ''), gender=nice_auth.get('gender', ''),
            join_safe_di=di, join_ncsafe=nice_auth.get('ci', ''),
            join_safegbn='M', sms_consent='Y', mail_consent='N', status='N',
        )
        user.set_password(pwd1)
        user.save()
        request.session.pop('nice_auth', None)
        login(request, user)
        messages.success(request, '회원가입이 완료되었습니다.')
        return redirect('/')

    return render(request, 'accounts/register_step2.html', {'nice_auth': nice_auth})


# ── NICE 통합인증 (회원가입 휴대폰 본인확인) ──

def nice_start(request):
    """휴대폰 본인인증 시작 — 토큰/인증창 URL 발급 후 NICE 표준창으로 이동(팝업 내)."""
    token = nice.get_access_token()
    if not token:
        return _nice_fail('본인인증 설정 오류입니다. 관리자에게 문의하세요.')
    # 콜백(return_url)은 접속한 호스트 기준으로 동적 생성 → 로컬/EC2/도메인 자동 대응.
    # settings.NICE_RETURN_URL 이 명시돼 있으면 그 값을 우선(고정 URL 강제 필요 시).
    return_url = settings.NICE_RETURN_URL or request.build_absolute_uri(
        reverse('accounts:nice_callback'))
    info = nice.request_auth_url(token['access_token'], return_url=return_url)
    if not info:
        return _nice_fail('본인인증 요청에 실패했습니다. 잠시 후 다시 시도하세요.')
    # 콜백 복호화에 필요한 값 세션 보관 (트랜잭션 10분 유효)
    request.session['nice_pending'] = {
        'access_token': token['access_token'],
        'ticket': token.get('ticket', ''),
        'iterators': token.get('iterators', ''),
        'transaction_id': info['transaction_id'],
        'request_no': info['request_no'],
        'purpose': request.GET.get('purpose', 'join'),   # join/findid/findpw
        'userid': request.GET.get('userid', ''),         # findpw 대상 아이디
    }
    return redirect(info['auth_url'])


@csrf_exempt
def nice_callback(request):
    """NICE 인증 결과 콜백(return_url) — 결과조회+복호화 후 부모창(회원가입폼) 자동입력."""
    pending = request.session.get('nice_pending')
    if not pending:
        return _nice_fail('본인인증 세션이 만료되었습니다. 다시 시도하세요.')
    web_tx = (request.POST.get('web_transaction_id')
              or request.GET.get('web_transaction_id', ''))
    if not web_tx:
        return _nice_fail('본인인증이 취소되었거나 실패했습니다.')

    result = nice.request_result(
        pending['access_token'], web_tx,
        pending['transaction_id'], pending['request_no'])
    if not result:
        return _nice_fail('인증 결과 조회에 실패했습니다.')

    info = nice.decrypt_result(
        result['enc_data'], result.get('integrity_value', ''),
        pending['ticket'], pending['transaction_id'], pending['iterators'])
    if not info:
        return _nice_fail('인증 결과 복호화에 실패했습니다.')

    purpose = pending.get('purpose', 'join')
    di = info.get('di', '')
    request.session.pop('nice_pending', None)

    # 아이디 찾기 — DI로 회원 조회
    if purpose == 'findid':
        member = Member.objects.filter(join_safe_di=di).first() if di else None
        if not member:
            return render(request, 'accounts/nice_callback.html',
                          {'action': 'findid', 'error': '회원정보가 존재하지 않습니다.'})
        return render(request, 'accounts/nice_callback.html',
                      {'action': 'findid', 'found_id': member.username})

    # 비밀번호 찾기 — DI + 입력 아이디 일치 시 임시비번 발급
    if purpose == 'findpw':
        userid = pending.get('userid', '')
        member = Member.objects.filter(join_safe_di=di).first() if di else None
        if not member:
            return render(request, 'accounts/nice_callback.html',
                          {'action': 'findpw', 'error': '등록된 사용자가 아닙니다.'})
        if member.username != userid:
            return render(request, 'accounts/nice_callback.html',
                          {'action': 'findpw', 'error': '아이디를 확인하여 주세요.'})
        temp_pw = _gen_temp_pw()
        member.set_password(temp_pw)
        member.failed_count = 0
        member.save(update_fields=['password', 'failed_count'])
        return render(request, 'accounts/nice_callback.html',
                      {'action': 'findpw', 'temp_pw': temp_pw})

    # 회원가입 — 인증값을 서버 세션에 보관 (폼 위변조 방지)
    gender = str(info.get('gender', ''))
    gender = {'1': 'M', '0': 'F'}.get(gender, gender)  # NICE 코드 → M/F
    phone = info.get('mobileno') or info.get('mobile_no') or ''
    request.session['nice_auth'] = {
        'name': info.get('name', ''),
        'birth': info.get('birthdate', ''),   # YYYYMMDD
        'gender': gender,
        'di': di,
        'ci': info.get('ci', ''),
        'phone': phone,
        'verified': True,
    }
    return render(request, 'accounts/nice_callback.html', {'action': 'join_step2'})


def _nice_fail(msg):
    """본인인증 팝업 내 실패 처리 — alert 후 팝업 닫기."""
    return HttpResponse(
        f'<script>alert("{msg}");try{{window.close();}}catch(e){{}}</script>')


def _gen_temp_pw(length=10):
    """임시 비밀번호 (영문+숫자 혼합, 회원 비번 규칙 충족)."""
    chars = string.ascii_letters + string.digits
    while True:
        pw = ''.join(secrets.choice(chars) for _ in range(length))
        if any(c.isalpha() for c in pw) and any(c.isdigit() for c in pw):
            return pw


# ── 약관/찾기 페이지 (ASP member/terms·privacy·id_search·pw_search.asp) ──

def terms_view(request):
    """이용약관"""
    return render(request, 'accounts/terms.html')


def privacy_view(request):
    """개인정보처리방침"""
    return render(request, 'accounts/privacy.html')


def id_search_view(request):
    """아이디 찾기 — NICE 본인인증으로 진행"""
    return render(request, 'accounts/id_search.html')


def pw_search_view(request):
    """비밀번호 찾기 — NICE 본인인증으로 진행"""
    return render(request, 'accounts/pw_search.html')


def logout_view(request):
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('/')


@login_required
def mypage_view(request):
    children = request.user.children.filter(status='N')
    return render(request, 'accounts/mypage.html', {'children': children})


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '프로필이 수정되었습니다.')
            return redirect('accounts:mypage')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def child_add_view(request):
    if request.method == 'POST':
        form = MemberChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user
            child.save()
            messages.success(request, '자녀가 등록되었습니다.')
            return redirect('accounts:mypage')
    else:
        form = MemberChildForm()
    return render(request, 'accounts/child_form.html', {'form': form, 'title': '자녀정보추가'})


@login_required
def child_edit_view(request, pk):
    child = get_object_or_404(MemberChild, pk=pk, parent=request.user)
    if request.method == 'POST':
        form = MemberChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, '자녀 정보가 수정되었습니다.')
            return redirect('accounts:mypage')
    else:
        form = MemberChildForm(instance=child)
    return render(request, 'accounts/child_form.html', {
        'form': form, 'title': '자녀정보수정', 'is_edit': True, 'child': child
    })


@login_required
def child_delete_view(request, pk):
    child = get_object_or_404(MemberChild, pk=pk, parent=request.user)
    if request.method == 'POST':
        child.delete()
        messages.success(request, '자녀가 삭제되었습니다.')
        return redirect('accounts:mypage')
    return render(request, 'accounts/child_confirm_delete.html', {'child': child})


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:mypage')

    def form_valid(self, form):
        messages.success(self.request, '비밀번호가 변경되었습니다.')
        return super().form_valid(form)
