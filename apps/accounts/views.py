from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from .forms import LoginForm, RegisterForm, ProfileForm, MemberChildForm, CustomPasswordChangeForm
from .models import MemberChild


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다.')
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('/')


@login_required
def mypage_view(request):
    children = request.user.children.all()
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
    return render(request, 'accounts/child_form.html', {'form': form, 'title': '자녀 등록'})


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
    return render(request, 'accounts/child_form.html', {'form': form, 'title': '자녀 수정'})


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
