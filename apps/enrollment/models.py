from django.db import models
from django.conf import settings


class Enrollment(models.Model):
    """입단 마스터 (lf_fcjoin_master)"""
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='enrollments', verbose_name='학부모',
        to_field='username', db_column='member_id',
    )
    child = models.ForeignKey(
        'accounts.MemberChild', on_delete=models.CASCADE,
        related_name='enrollments', verbose_name='자녀',
        to_field='child_id', db_column='child_id',
    )
    pay_stats = models.CharField('결제상태', max_length=2, default='UN',
        choices=[('PY', '결제완료'), ('UN', '미결제'), ('PP', '부분결제'), ('PN', '결제대기'), ('PQ', '환불'), ('PZ', '취소')])
    pay_method = models.CharField('결제방법', max_length=10, blank=True,
        choices=[('CARD', '카드'), ('R', '계좌이체'), ('VACCT', '가상계좌'),
                 ('ACCT', '계좌'), ('BENEFIT', '복지'), ('ZEROPAY', '제로페이'),
                 ('MUCU', '문화상품권'), ('LOTTE', '롯데'), ('ESNC', 'ESNC'),
                 ('GRPY', '그룹페이'), ('EMART', '이마트'), ('SPBA', 'SPBA')])
    pay_price = models.IntegerField('결제금액', default=0)
    pay_dt = models.DateTimeField('결제일시', null=True, blank=True)
    lecture_stats = models.CharField('수강상태', max_length=2, default='LN',
        choices=[('LY', '수강확정'), ('LP', '일시정지'), ('LN', '취소'), ('PN', '대기')])
    lec_cycle = models.IntegerField('주간횟수', default=1)
    lec_period = models.IntegerField('수강기간(월)', default=3)
    start_dt = models.CharField('시작년월', max_length=6, blank=True)
    end_dt = models.CharField('종료년월', max_length=6, blank=True)
    apply_gubun = models.CharField('신청구분', max_length=5, default='NEW',
        choices=[('NEW', '신규'), ('RE', '재등록'), ('RENEW', '갱신'), ('AGAIN', '재입단')])
    source_gubun = models.CharField('신청출처', max_length=2, default='01')
    recommend_id = models.CharField('추천인ID', max_length=30, blank=True)
    # 6개 할인 슬롯
    discount1_id = models.CharField('할인1 ID', max_length=30, blank=True)
    discount1_price = models.IntegerField('할인1 금액', default=0)
    discount2_id = models.CharField('할인2 ID', max_length=30, blank=True)
    discount2_price = models.IntegerField('할인2 금액', default=0)
    discount3_id = models.CharField('할인3 ID', max_length=30, blank=True)
    discount3_price = models.IntegerField('할인3 금액', default=0)
    discount4_id = models.CharField('할인4 ID', max_length=30, blank=True)
    discount4_price = models.IntegerField('할인4 금액', default=0)
    discount5_id = models.CharField('할인5 ID', max_length=30, blank=True)
    discount5_price = models.IntegerField('할인5 금액', default=0)
    discount6_id = models.CharField('할인6 ID', max_length=30, blank=True)
    discount6_price = models.IntegerField('할인6 금액', default=0)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_id = models.CharField('등록자', max_length=30, blank=True)
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'enrollment_enrollment'
        verbose_name = '입단신청'
        verbose_name_plural = '입단신청'
        ordering = ['-id']

    def __str__(self):
        return f'#{self.id} {self.member_id} - {self.child_id}'


class EnrollmentCourse(models.Model):
    """수강과정 월별 (lf_fcjoin_course)"""
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE,
        related_name='courses', verbose_name='입단',
        db_column='no_seq',
    )
    bill_code = models.CharField('청구코드', max_length=4)
    course_ym = models.DateField('수강년월')
    course_ym_amt = models.IntegerField('수강금액', default=0)
    lecture_code = models.IntegerField('강좌코드', default=0)
    start_ymd = models.DateField('시작일', null=True, blank=True)
    course_stats = models.CharField('수강상태', max_length=2, default='LY')

    class Meta:
        db_table = 'enrollment_enrollmentcourse'
        verbose_name = '수강과정'
        verbose_name_plural = '수강과정'

    def __str__(self):
        return f'입단#{self.enrollment_id} {self.bill_code} {self.course_ym}'


class EnrollmentBill(models.Model):
    """청구내역 (lf_fcjoin_bill)"""
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE,
        related_name='bills', verbose_name='입단',
        db_column='no_seq',
    )
    bill_code = models.CharField('청구코드', max_length=4)
    bill_desc = models.CharField('청구설명', max_length=100, blank=True)
    bill_amt = models.IntegerField('청구금액', default=0)
    pay_stats = models.CharField('결제상태', max_length=2, default='UN')
    insert_id = models.CharField('등록자', max_length=30, blank=True)
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'enrollment_enrollmentbill'
        verbose_name = '청구내역'
        verbose_name_plural = '청구내역'

    def __str__(self):
        return f'입단#{self.enrollment_id} {self.bill_code} {self.bill_amt}'


class WaitStudent(models.Model):
    """대기자 (lf_wait_student)"""
    local_code = models.IntegerField('권역코드', default=0)
    sta_code = models.IntegerField('구장코드', default=0)
    lecture_code = models.IntegerField('강좌코드', default=0)
    member_id = models.CharField('학부모 아이디', max_length=30)
    member_name = models.CharField('학부모 이름', max_length=60, blank=True)
    child_id = models.CharField('자녀 아이디', max_length=25)
    child_name = models.CharField('자녀 이름', max_length=20, blank=True)
    wait_seq = models.IntegerField('대기순번', default=0)
    trans_gbn = models.CharField('전환여부', max_length=1, default='N')
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_id = models.CharField('등록자', max_length=30, blank=True)
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'enrollment_waitstudent'
        verbose_name = '대기자'
        verbose_name_plural = '대기자'

    def __str__(self):
        return f'{self.child_name} - 대기#{self.wait_seq}'
