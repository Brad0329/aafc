from django.conf import settings
from django.db import models


class Notification(models.Model):
    """알림장 (lf_alim) - 코치→학부모 알림"""
    ALIM_GBN_CHOICES = [
        ('P', '학부모'),
    ]

    no_seq = models.IntegerField('알림번호', unique=True)
    alim_gbn = models.CharField('알림구분', max_length=1, default='P', choices=ALIM_GBN_CHOICES)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications', verbose_name='회원',
        to_field='username', db_column='member_id',
    )
    member_name = models.CharField('회원명', max_length=20, blank=True)
    child_id = models.CharField('자녀ID', max_length=16, blank=True)
    local_code = models.IntegerField('권역코드', null=True, blank=True)
    sta_code = models.IntegerField('구장코드', null=True, blank=True)
    lecture_code = models.IntegerField('강좌코드', null=True, blank=True)
    alim_title = models.CharField('제목', max_length=100)
    alim_content = models.TextField('내용', blank=True)
    alim_file = models.CharField('첨부파일', max_length=200, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_id = models.CharField('작성자ID', max_length=12, blank=True)
    insert_name = models.CharField('작성자명', max_length=20, blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'notifications_notification'
        verbose_name = '알림장'
        verbose_name_plural = '알림장'
        ordering = ['-insert_dt']

    def __str__(self):
        return f'{self.alim_title} ({self.member_name})'


class OfficeNotification(models.Model):
    """사무실 알림 (lf_office_alim) - 관리자 공지"""
    no_seq = models.IntegerField('알림번호', unique=True)
    atitle = models.CharField('제목', max_length=100)
    acontent = models.TextField('내용', blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    reg_dt = models.DateTimeField('등록일', null=True, blank=True)
    reg_id = models.CharField('등록자ID', max_length=20, blank=True)

    class Meta:
        db_table = 'notifications_officenotification'
        verbose_name = '사무실 알림'
        verbose_name_plural = '사무실 알림'
        ordering = ['-reg_dt']

    def __str__(self):
        return self.atitle


class SMSLog(models.Model):
    """SMS 발송 로그 (em_mmt_tran_log_kyt)"""
    SERVICE_TYPE_CHOICES = [
        ('0', 'SMS'),
        ('2', 'SMS'),
        ('3', 'LMS'),
    ]

    msg_key = models.CharField('메시지키', max_length=20, blank=True)
    date_client_req = models.DateTimeField('발송요청일시', null=True, blank=True)
    subject = models.CharField('제목', max_length=40, blank=True)
    content = models.TextField('내용', blank=True)
    callback = models.CharField('발신번호', max_length=25, blank=True)
    service_type = models.CharField('서비스유형', max_length=2, blank=True, choices=SERVICE_TYPE_CHOICES)
    msg_status = models.CharField('발송상태', max_length=1, blank=True)
    recipient_num = models.CharField('수신번호', max_length=25, blank=True)
    broadcast_yn = models.CharField('대량발송여부', max_length=1, default='N')
    date_sent = models.DateTimeField('발송일시', null=True, blank=True)
    date_rslt = models.DateTimeField('결과수신일시', null=True, blank=True)
    rslt = models.CharField('발송결과', max_length=10, blank=True)

    class Meta:
        db_table = 'notifications_smslog'
        verbose_name = 'SMS 로그'
        verbose_name_plural = 'SMS 로그'
        ordering = ['-date_client_req']

    def __str__(self):
        return f'{self.recipient_num} ({self.date_client_req})'
