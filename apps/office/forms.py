from django import forms


class OfficeLoginForm(forms.Form):
    login_id = forms.CharField(max_length=12)
    login_pwd = forms.CharField(max_length=50, widget=forms.PasswordInput)
