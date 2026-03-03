from django.db import models


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
