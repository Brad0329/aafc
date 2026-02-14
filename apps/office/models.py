from django.db import models


class OfficeUser(models.Model):
    """관리자 사용자 (lf_officeuser)"""

    USE_AUTH_CHOICES = [
        ('W', '주니어'),
        ('E', '이마트'),
    ]

    office_code = models.AutoField('관리자코드', primary_key=True)
    office_name = models.CharField('표시명', max_length=30)
    office_realname = models.CharField('실명', max_length=30, blank=True)
    office_id = models.CharField('아이디', max_length=12, unique=True)
    office_pwd = models.CharField('비밀번호', max_length=200)
    office_part = models.CharField('부서명', max_length=20, blank=True)
    office_mail = models.CharField('이메일', max_length=128, blank=True)
    office_hp = models.CharField('연락처', max_length=20, blank=True)
    power_level = models.CharField('메뉴권한', max_length=40, blank=True)
    use_auth = models.CharField('접속구분', max_length=2, default='W', choices=USE_AUTH_CHOICES)
    coach_code = models.CharField('코치코드', max_length=30, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'office_officeuser'
        verbose_name = '관리자'
        verbose_name_plural = '관리자'
        ordering = ['office_name']

    def __str__(self):
        return f'{self.office_name} ({self.office_id})'

    def has_permission(self, code):
        """특정 메뉴 권한 보유 여부 확인"""
        return code in (self.power_level or '')


class OfficeLoginHistory(models.Model):
    """관리자 로그인 이력"""
    office_id = models.CharField('관리자ID', max_length=12)
    login_dt = models.DateTimeField('로그인일시', auto_now_add=True)
    login_ip = models.CharField('접속IP', max_length=45, blank=True)

    class Meta:
        db_table = 'office_loginhistory'
        verbose_name = '관리자 로그인 이력'
        verbose_name_plural = '관리자 로그인 이력'
        ordering = ['-login_dt']

    def __str__(self):
        return f'{self.office_id} ({self.login_dt})'
