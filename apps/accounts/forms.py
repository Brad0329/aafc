from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import Member, MemberChild


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='아이디')
    password = forms.CharField(label='비밀번호', widget=forms.PasswordInput)


class RegisterForm(UserCreationForm):
    class Meta:
        model = Member
        fields = ['username', 'name', 'email', 'phone', 'zipcode', 'address1', 'address2']
        labels = {
            'username': '아이디',
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['email', 'phone', 'tel', 'zipcode', 'address1', 'address2',
                  'sms_consent', 'mail_consent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sms_consent'].widget = forms.RadioSelect(
            choices=[('Y', '동의함'), ('N', '동의안함')]
        )
        self.fields['mail_consent'].widget = forms.RadioSelect(
            choices=[('Y', '동의함'), ('N', '동의안함')]
        )


class MemberChildForm(forms.ModelForm):
    class Meta:
        model = MemberChild
        fields = ['name', 'birth', 'gender', 'school', 'grade']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].widget = forms.Select(
            choices=[('M', '남자'), ('F', '여자')]
        )


class CustomPasswordChangeForm(PasswordChangeForm):
    pass
