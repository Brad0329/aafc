from django.db import models


class PaymentKCP(models.Model):
    """KCP 결제 로그 (lf_pay_kcp + lf_pay_kcp_log)"""
    req_tx = models.CharField('요청타입', max_length=10, blank=True)
    use_pay_method = models.CharField('결제수단코드', max_length=20, blank=True)
    bsucc = models.CharField('성공여부', max_length=5, blank=True)
    res_cd = models.CharField('응답코드', max_length=10, blank=True)
    res_msg = models.CharField('응답메시지', max_length=200, blank=True)
    res_msg_bsucc = models.CharField('성공메시지', max_length=200, blank=True)
    amount = models.IntegerField('결제금액', default=0)
    ordr_idxx = models.CharField('주문번호', max_length=100, blank=True)
    tno = models.CharField('거래번호', max_length=100, blank=True)
    good_mny = models.IntegerField('상품금액', default=0)
    good_name = models.CharField('상품명', max_length=200, blank=True)
    buyr_name = models.CharField('구매자명', max_length=60, blank=True)
    buyr_tel1 = models.CharField('구매자전화1', max_length=20, blank=True)
    buyr_tel2 = models.CharField('구매자전화2', max_length=20, blank=True)
    buyr_mail = models.CharField('구매자메일', max_length=100, blank=True)
    app_time = models.CharField('승인시간', max_length=20, blank=True)
    card_cd = models.CharField('카드코드', max_length=10, blank=True)
    card_name = models.CharField('카드명', max_length=50, blank=True)
    app_no = models.CharField('승인번호', max_length=20, blank=True)
    noinf = models.CharField('무이자여부', max_length=5, blank=True)
    quota = models.CharField('할부개월', max_length=3, blank=True)
    bank_name = models.CharField('은행명', max_length=20, blank=True)
    bank_code = models.CharField('은행코드', max_length=10, blank=True)
    depositor = models.CharField('예금주', max_length=20, blank=True)
    account = models.CharField('계좌번호', max_length=30, blank=True)
    va_date = models.CharField('가상계좌입금기한', max_length=20, blank=True)
    pay_seq = models.IntegerField('입단번호', default=0)
    member_num = models.CharField('회원아이디', max_length=30, blank=True)
    pg_gbn = models.CharField('PG구분', max_length=5, blank=True)
    add_pnt = models.IntegerField('추가포인트', default=0)
    use_pnt = models.IntegerField('사용포인트', default=0)
    rsv_pnt = models.IntegerField('적립포인트', default=0)
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'payments_paymentkcp'
        verbose_name = 'KCP결제'
        verbose_name_plural = 'KCP결제'
        ordering = ['-id']

    def __str__(self):
        return f'#{self.id} {self.ordr_idxx} {self.amount}'


class PaymentFail(models.Model):
    """결제 실패 로그 (lf_pay_kcp_faillog)"""
    req_tx = models.CharField('요청타입', max_length=10, blank=True)
    use_pay_method = models.CharField('결제수단코드', max_length=20, blank=True)
    res_cd = models.CharField('응답코드', max_length=10, blank=True)
    res_msg = models.CharField('응답메시지', max_length=200, blank=True)
    amount = models.IntegerField('결제금액', default=0)
    ordr_idxx = models.CharField('주문번호', max_length=100, blank=True)
    good_name = models.CharField('상품명', max_length=200, blank=True)
    buyr_name = models.CharField('구매자명', max_length=60, blank=True)
    member_num = models.CharField('회원아이디', max_length=30, blank=True)
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'payments_paymentfail'
        verbose_name = '결제실패'
        verbose_name_plural = '결제실패'
        ordering = ['-id']

    def __str__(self):
        return f'#{self.id} {self.ordr_idxx} FAIL'
