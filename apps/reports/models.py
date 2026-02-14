from django.db import models


class DailyTotalData(models.Model):
    """전체 DATA (lf_daily_total_data)"""
    proc_dt = models.CharField('처리일', max_length=12, blank=True)
    member_id = models.CharField('학부모ID', max_length=30, blank=True)
    member_name = models.CharField('학부모명', max_length=30, blank=True)
    child_id = models.CharField('자녀ID', max_length=30, blank=True)
    mhtel = models.CharField('연락처', max_length=30, blank=True)
    child_name = models.CharField('자녀명', max_length=30, blank=True)
    card_num = models.CharField('카드번호', max_length=8, blank=True)
    apply_gubun = models.CharField('신청구분', max_length=30, blank=True)
    sta_name = models.CharField('구장명', max_length=50, blank=True)
    lecture_code = models.IntegerField('강좌코드', default=0)
    lecture_title = models.CharField('강좌명', max_length=150, blank=True)
    coach_name = models.CharField('코치명', max_length=30, blank=True)
    lec_cycle = models.CharField('주간횟수', max_length=1, blank=True)
    lec_period = models.CharField('수강기간', max_length=1, blank=True)
    lecture_stats = models.CharField('수강상태', max_length=30, blank=True)
    pay_price = models.IntegerField('결제금액', default=0)
    lec_price = models.IntegerField('수업료', default=0)
    join_price = models.IntegerField('입단비', default=0)
    lec_course_ym_amt = models.IntegerField('월수강금액', default=0)
    pay_stats = models.CharField('결제상태', max_length=12, blank=True)
    pay_method = models.CharField('결제방법', max_length=14, blank=True)
    pay_dt = models.CharField('결제일', max_length=10, blank=True)
    cancel_date = models.CharField('취소일', max_length=10, blank=True)
    cancel_code = models.CharField('취소코드', max_length=4, blank=True)
    cancel_desc = models.CharField('취소사유', max_length=100, blank=True)
    start_dt = models.CharField('시작년월', max_length=6, blank=True)
    end_dt = models.CharField('종료년월', max_length=6, blank=True)
    course_ym = models.CharField('수강년월', max_length=7, blank=True)
    course_ym_amt = models.IntegerField('수강년월금액', default=0)
    insert_id = models.CharField('등록자', max_length=16, blank=True)
    insert_dt = models.CharField('등록일', max_length=10, blank=True)

    class Meta:
        db_table = 'reports_dailytotaldata'
        verbose_name = '전체 DATA'
        verbose_name_plural = '전체 DATA'
        indexes = [
            models.Index(fields=['proc_dt'], name='idx_dtd_proc_dt'),
            models.Index(fields=['member_id'], name='idx_dtd_member'),
            models.Index(fields=['sta_name'], name='idx_dtd_sta'),
            models.Index(fields=['course_ym'], name='idx_dtd_course_ym'),
            models.Index(fields=['pay_stats'], name='idx_dtd_pay_stats'),
        ]

    def __str__(self):
        return f'{self.proc_dt} {self.member_name} {self.child_name}'


class DailyCoachData(models.Model):
    """코치별 DATA (lf_daily_coachdata)"""
    course_ym = models.CharField('수강년월', max_length=10, blank=True)
    lgbn_name = models.CharField('리그구분', max_length=30, blank=True)
    sta_name = models.CharField('구장명', max_length=40, blank=True)
    coach_name = models.CharField('코치명', max_length=40, blank=True)
    member_id = models.CharField('학부모ID', max_length=30, blank=True)
    child_id = models.CharField('자녀ID', max_length=30, blank=True)
    cl_cnt = models.IntegerField('수업횟수', default=0)
    m1001_price = models.IntegerField('수업료', default=0)
    m1002_price = models.IntegerField('프로모션', default=0)
    m10031_price = models.IntegerField('상품비1', default=0)
    m10032_price = models.IntegerField('상품비2', default=0)
    m1007_price = models.IntegerField('기타', default=0)
    m2001_price = models.IntegerField('교육용품1', default=0)
    m2002_price = models.IntegerField('교육용품2', default=0)
    regdate = models.DateTimeField('등록일', null=True, blank=True)
    master_seq = models.IntegerField('입단번호', default=0)

    class Meta:
        db_table = 'reports_dailycoachdata'
        verbose_name = '코치별 DATA'
        verbose_name_plural = '코치별 DATA'
        indexes = [
            models.Index(fields=['course_ym'], name='idx_dcd_course_ym'),
        ]

    def __str__(self):
        return f'{self.course_ym} {self.coach_name} {self.sta_name}'


class DailyCoachDataNew(models.Model):
    """코치별 DATA (신규) (lf_daily_coachdata_new)"""
    proc_dt = models.CharField('처리일', max_length=8, blank=True)
    pay_seq = models.IntegerField('결제번호', default=0)
    member_id = models.CharField('학부모ID', max_length=30, blank=True)
    child_id = models.CharField('자녀ID', max_length=30, blank=True)
    order_id = models.CharField('주문ID', max_length=50, blank=True)
    pay_dt = models.DateTimeField('결제일', null=True, blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    pay_method = models.CharField('결제방법', max_length=20, blank=True)
    course_ym = models.CharField('수강년월', max_length=10, blank=True)
    sta_code = models.IntegerField('구장코드', default=0)
    lecture_code = models.IntegerField('강좌코드', default=0)
    coach_code = models.IntegerField('코치코드', default=0)
    coach_name = models.CharField('코치명', max_length=30, blank=True)
    cl_cnt = models.IntegerField('수업횟수', default=0)
    m1001_price = models.IntegerField('수업료', default=0)
    m1002_price = models.IntegerField('프로모션', default=0)
    m1003_price = models.IntegerField('상품비', default=0)
    m1003_b_price = models.IntegerField('상품비B', default=0)
    m1006_price = models.IntegerField('기타1', default=0)
    m1007_b_price = models.IntegerField('기타2B', default=0)
    m1009_b_price = models.IntegerField('기타3B', default=0)
    m2001_price = models.IntegerField('교육용품1', default=0)
    m2002_price = models.IntegerField('교육용품2', default=0)
    regdate = models.DateTimeField('등록일시', null=True, blank=True)

    class Meta:
        db_table = 'reports_dailycoachdatanew'
        verbose_name = '코치별 DATA(신규)'
        verbose_name_plural = '코치별 DATA(신규)'
        indexes = [
            models.Index(fields=['course_ym'], name='idx_dcdn_course_ym'),
            models.Index(fields=['proc_dt'], name='idx_dcdn_proc_dt'),
        ]

    def __str__(self):
        return f'{self.course_ym} {self.coach_name} {self.proc_dt}'


class DailyCoachDataMonth(models.Model):
    """코치별 월별 DATA (lf_daily_coachdata_new_month)"""
    pay_seq = models.IntegerField('결제번호', default=0)
    member_id = models.CharField('학부모ID', max_length=30, blank=True)
    child_id = models.CharField('자녀ID', max_length=30, blank=True)
    order_id = models.CharField('주문ID', max_length=50, blank=True)
    pay_dt = models.DateTimeField('결제일', null=True, blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    pay_method = models.CharField('결제방법', max_length=20, blank=True)
    course_ym = models.CharField('수강년월', max_length=10, blank=True)
    sta_code = models.IntegerField('구장코드', default=0)
    lecture_code = models.IntegerField('강좌코드', default=0)
    coach_code = models.IntegerField('코치코드', default=0)
    coach_name = models.CharField('코치명', max_length=30, blank=True)
    cl_cnt = models.IntegerField('수업횟수', default=0)
    m1001_price = models.IntegerField('수업료', default=0)
    m1002_price = models.IntegerField('프로모션', default=0)
    m1003_price = models.IntegerField('상품비', default=0)
    m1003_b_price = models.IntegerField('상품비B', default=0)
    m1006_price = models.IntegerField('기타1', default=0)
    m1007_b_price = models.IntegerField('기타2B', default=0)
    m1009_b_price = models.IntegerField('기타3B', default=0)
    m2001_price = models.IntegerField('교육용품1', default=0)
    m2002_price = models.IntegerField('교육용품2', default=0)
    regdate = models.DateTimeField('등록일시', null=True, blank=True)
    new_coach_code = models.IntegerField('변경코치코드', default=0)
    new_coach_name = models.CharField('변경코치명', max_length=30, blank=True)

    class Meta:
        db_table = 'reports_dailycoachdatamonth'
        verbose_name = '코치별 월별 DATA'
        verbose_name_plural = '코치별 월별 DATA'
        indexes = [
            models.Index(fields=['course_ym'], name='idx_dcdm_course_ym'),
        ]

    def __str__(self):
        return f'{self.course_ym} {self.coach_name}'


class MonthlyData(models.Model):
    """월별 통계 (lf_monthly_data)"""
    proc_dt = models.CharField('처리일', max_length=20, blank=True)
    code_desc = models.CharField('코드설명', max_length=50, blank=True)
    sta_name = models.CharField('구장명', max_length=50, blank=True)
    sta_code = models.IntegerField('구장코드', default=0)
    m_cnt = models.IntegerField('회원수', default=0)
    goal_cnt = models.IntegerField('목표수', default=0)
    tocl = models.IntegerField('총수업', default=0)
    newT_appl_cnt = models.IntegerField('신규체험신청', default=0)
    newF_appl_cnt = models.IntegerField('신규유료신청', default=0)
    renewT_appl_cnt = models.IntegerField('갱신체험신청', default=0)
    renewF_appl_cnt = models.IntegerField('갱신유료신청', default=0)
    again_appl_cnt = models.IntegerField('재입단신청', default=0)
    stats_tot_cnt = models.IntegerField('통계전체', default=0)
    stats_ln_cnt = models.IntegerField('통계수강', default=0)
    stats_lnT_cnt = models.IntegerField('통계수강체험', default=0)
    stats_lnF_cnt = models.IntegerField('통계수강유료', default=0)
    regdate = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'reports_monthlydata'
        verbose_name = '월별 통계'
        verbose_name_plural = '월별 통계'
        indexes = [
            models.Index(fields=['proc_dt'], name='idx_md_proc_dt'),
            models.Index(fields=['sta_code'], name='idx_md_sta_code'),
        ]

    def __str__(self):
        return f'{self.proc_dt} {self.sta_name}'
