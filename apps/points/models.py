from django.conf import settings
from django.db import models


class PointConfig(models.Model):
    """포인트 설정 (lf_point_set)"""
    APP_GBN_CHOICES = [
        ('S', '적립'),
        ('U', '사용'),
    ]
    SAVE_GBN_CHOICES = [
        ('PE', '비율(%)'),
        ('PO', '정액(포인트)'),
    ]

    point_seq = models.CharField('포인트코드', max_length=4, unique=True)
    point_title = models.CharField('포인트명', max_length=30)
    use_yn = models.CharField('사용여부', max_length=2, default='Y')
    app_gbn = models.CharField('적립/사용구분', max_length=2, choices=APP_GBN_CHOICES)
    save_gbn = models.CharField('적립방식', max_length=2, choices=SAVE_GBN_CHOICES, blank=True)
    save_point = models.IntegerField('적립포인트/비율', default=0)
    limit_point = models.IntegerField('기준금액/최소사용금액', default=0)

    class Meta:
        db_table = 'points_pointconfig'
        verbose_name = '포인트 설정'
        verbose_name_plural = '포인트 설정'
        ordering = ['point_seq']

    def __str__(self):
        return f'[{self.point_seq}] {self.point_title}'


class PointHistory(models.Model):
    """포인트 내역 (lf_userpoint_his)"""
    APP_GBN_CHOICES = [
        ('S', '적립'),
        ('U', '사용'),
    ]

    point_dt = models.CharField('포인트일자', max_length=12, blank=True)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='point_histories', verbose_name='회원',
        to_field='username', db_column='member_id',
    )
    member_name = models.CharField('회원명', max_length=20, blank=True)
    app_gbn = models.CharField('적립/사용', max_length=2, choices=APP_GBN_CHOICES)
    app_point = models.IntegerField('포인트', default=0)
    point_desc = models.CharField('내용', max_length=200, blank=True)
    order_no = models.CharField('주문번호', max_length=100, blank=True)
    confirm_id = models.CharField('확인자ID', max_length=100, blank=True)
    desc_detail = models.CharField('상세내용', max_length=1000, blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    insert_id = models.CharField('등록자', max_length=20, blank=True)

    class Meta:
        db_table = 'points_pointhistory'
        verbose_name = '포인트 내역'
        verbose_name_plural = '포인트 내역'
        ordering = ['-insert_dt', '-id']

    def __str__(self):
        gbn = '적립' if self.app_gbn == 'S' else '사용'
        return f'{self.member_id} {gbn} {self.app_point}P - {self.point_desc}'
