from django.contrib.auth.models import AbstractUser
from django.db import models


class Member(AbstractUser):
    """회원/학부모 (lf_member)"""

    # AbstractUser 기본 필드 활용: username(=member_id), password, email, last_login
    # first_name, last_name 대신 name 사용
    first_name = None
    last_name = None

    member_code = models.IntegerField('회원코드(레거시)', unique=True, null=True, blank=True)
    name = models.CharField('이름', max_length=60, blank=True)
    tel = models.CharField('전화번호', max_length=14, blank=True)
    phone = models.CharField('휴대전화', max_length=14, blank=True)
    zipcode = models.CharField('우편번호', max_length=7, blank=True)
    address1 = models.CharField('주소', max_length=100, blank=True)
    address2 = models.CharField('상세주소', max_length=100, blank=True)
    sms_consent = models.CharField('SMS 수신동의', max_length=1, default='N')
    mail_consent = models.CharField('메일 수신동의', max_length=1, default='N')
    status = models.CharField('회원상태', max_length=1, default='N')
    login_count = models.IntegerField('로그인횟수', default=0)
    failed_count = models.IntegerField('로그인실패횟수', default=0)

    # NICE 본인인증 관련
    join_ncsafe = models.CharField('NICE 인증값', max_length=255, blank=True)
    birth = models.CharField('생년월일', max_length=12, blank=True)
    gender = models.CharField('성별', max_length=1, blank=True)
    join_safe_di = models.CharField('NICE DI', max_length=255, blank=True)
    join_ipin_key = models.CharField('아이핀 키', max_length=255, blank=True)
    join_safegbn = models.CharField('인증구분', max_length=20, blank=True)

    join_path = models.CharField('가입경로', max_length=2, blank=True)
    secession_desc = models.TextField('탈퇴사유', blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'accounts_member'
        verbose_name = '회원'
        verbose_name_plural = '회원'

    def __str__(self):
        return f'{self.username} ({self.name})'


class MemberChild(models.Model):
    """자녀 (lf_memberchild)"""

    child_code = models.IntegerField('자녀코드(레거시)', unique=True, null=True, blank=True)
    parent = models.ForeignKey(
        Member, on_delete=models.CASCADE,
        related_name='children', verbose_name='학부모',
        to_field='username', db_column='member_id',
    )
    name = models.CharField('이름', max_length=20, blank=True)
    child_id = models.CharField('자녀 아이디', max_length=25, unique=True)
    child_pwd = models.CharField('자녀 비밀번호', max_length=200, blank=True)
    birth = models.CharField('생년월일', max_length=12, blank=True)
    gender = models.CharField('성별', max_length=1, blank=True)
    school = models.CharField('학교', max_length=40, blank=True)
    grade = models.CharField('학년', max_length=20, blank=True)
    height = models.CharField('키', max_length=4, blank=True)
    weight = models.CharField('몸무게', max_length=4, blank=True)
    size = models.CharField('사이즈', max_length=4, blank=True)
    phone = models.CharField('휴대전화', max_length=14, blank=True)
    login_count = models.IntegerField('로그인횟수', default=0)
    status = models.CharField('상태', max_length=1, default='N')
    last_login = models.DateTimeField('마지막 로그인', null=True, blank=True)
    secession_desc = models.TextField('탈퇴사유', blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    join_path = models.CharField('가입경로', max_length=2, blank=True)
    card_num = models.CharField('카드번호', max_length=8, blank=True)
    course_state = models.CharField('수강상태', max_length=3, blank=True)

    class Meta:
        db_table = 'accounts_memberchild'
        verbose_name = '자녀'
        verbose_name_plural = '자녀'

    def __str__(self):
        return f'{self.name} ({self.parent_id})'


class OutMember(models.Model):
    """탈퇴회원 (lf_outmember)"""

    member_id = models.CharField('회원 아이디', max_length=30)
    member_name = models.CharField('회원 이름', max_length=30, blank=True)
    out_desc = models.TextField('탈퇴사유', blank=True)
    out_dt = models.DateTimeField('탈퇴일', null=True, blank=True)

    class Meta:
        db_table = 'accounts_outmember'
        verbose_name = '탈퇴회원'
        verbose_name_plural = '탈퇴회원'

    def __str__(self):
        return f'{self.member_id} ({self.member_name})'
