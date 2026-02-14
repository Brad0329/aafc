from django.db import models


class Consult(models.Model):
    """상담 (lf_consult)"""
    member_id = models.CharField('회원ID', max_length=16, blank=True)
    member_name = models.CharField('회원명', max_length=20, blank=True)
    child_id = models.CharField('자녀ID', max_length=16, blank=True)
    child_name = models.CharField('자녀명', max_length=20, blank=True)
    consult_name = models.CharField('신청자명', max_length=20)
    consult_tel = models.CharField('연락처', max_length=20, blank=True)
    consult_gbn = models.CharField('구분', max_length=10, blank=True)
    consult_title = models.CharField('제목', max_length=200, blank=True)
    consult_content = models.TextField('내용', blank=True)
    consult_pwd = models.CharField('비밀번호', max_length=4, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    consult_dt = models.DateTimeField('상담일시', null=True, blank=True)
    manage_id = models.CharField('관리자ID', max_length=16, blank=True)
    local_code = models.CharField('권역코드', max_length=20, blank=True)
    sta_code = models.CharField('구장코드', max_length=20, blank=True)
    stu_name = models.CharField('수강생명', max_length=30, blank=True)
    stu_sex = models.CharField('성별', max_length=1, blank=True)
    stu_age = models.IntegerField('나이', default=0)
    path_code = models.IntegerField('신청경로코드', default=44)
    line_code = models.IntegerField('접수경로코드', default=33)
    company_name = models.CharField('회사명', max_length=30, blank=True)
    com_employee_no = models.CharField('직원번호', max_length=10, blank=True)

    class Meta:
        db_table = 'consult_consult'
        verbose_name = '상담'
        verbose_name_plural = '상담'
        ordering = ['-id']

    def __str__(self):
        return f'{self.consult_name} - {self.consult_title}'


class ConsultAnswer(models.Model):
    """상담 답변 (lf_con_answer)"""
    consult = models.ForeignKey(
        Consult, on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='상담'
    )
    consult_category = models.IntegerField('상담분류코드', null=True, blank=True)
    consult_answer = models.TextField('답변', blank=True)
    con_answer_dt = models.DateTimeField('답변일시', null=True, blank=True)
    coach_code = models.IntegerField('담당코치코드', null=True, blank=True)
    stat_code = models.IntegerField('상담상태', default=76)
    receive_code = models.IntegerField('접수코드', null=True, blank=True)
    cus_stat_code = models.IntegerField('고객상태코드', null=True, blank=True)

    class Meta:
        db_table = 'consult_consultanswer'
        verbose_name = '상담답변'
        verbose_name_plural = '상담답변'

    def __str__(self):
        return f'답변 (상태: {self.stat_code})'


class ConsultFree(models.Model):
    """무료체험 신청 (lf_consult_free)"""
    jname = models.CharField('신청자명', max_length=20)
    jphone1 = models.CharField('전화1', max_length=5, blank=True)
    jphone2 = models.CharField('전화2', max_length=5, blank=True)
    jphone3 = models.CharField('전화3', max_length=5, blank=True)
    jlocal = models.CharField('지역', max_length=30, blank=True)
    j_date = models.DateTimeField('신청일', null=True, blank=True)
    confirm_memo = models.TextField('확인메모', blank=True)
    confirm_yn = models.CharField('확인여부', max_length=1, default='N')
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    confirm_id = models.CharField('확인자ID', max_length=20, blank=True)
    confirm_name = models.CharField('확인자명', max_length=20, blank=True)
    confirm_date = models.DateTimeField('확인일', null=True, blank=True)
    consult_gbn = models.CharField('구분', max_length=10, blank=True)

    class Meta:
        db_table = 'consult_consultfree'
        verbose_name = '무료체험신청'
        verbose_name_plural = '무료체험신청'
        ordering = ['-id']

    def __str__(self):
        return f'{self.jname} ({self.jlocal})'


class ConsultRegion(models.Model):
    """상담 지역설정 (lf_consult_uplocal)"""
    reg_gbn = models.CharField('등록구분', max_length=1, default='L')
    reg_name = models.CharField('지역명', max_length=100)
    mphone = models.CharField('담당자전화', max_length=20, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')

    class Meta:
        db_table = 'consult_consultregion'
        verbose_name = '상담지역'
        verbose_name_plural = '상담지역'
        ordering = ['reg_name']

    def __str__(self):
        return self.reg_name
