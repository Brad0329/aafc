from django.db import models


class CodeGroup(models.Model):
    """공통 코드 그룹 (lf_codegroup)"""
    grpcode = models.CharField('그룹코드', max_length=4, primary_key=True)
    grpcode_name = models.CharField('그룹명', max_length=20, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    insert_id = models.CharField('등록자', max_length=12, blank=True)

    class Meta:
        db_table = 'common_codegroup'
        verbose_name = '코드그룹'
        verbose_name_plural = '코드그룹'

    def __str__(self):
        return f'{self.grpcode} - {self.grpcode_name}'


class CodeValue(models.Model):
    """공통 코드 값 (lf_codesub)"""
    subcode = models.IntegerField('서브코드')
    group = models.ForeignKey(
        CodeGroup, on_delete=models.CASCADE,
        related_name='codes', db_column='grpcode',
        verbose_name='그룹코드'
    )
    code_name = models.CharField('코드명', max_length=40, blank=True)
    code_desc = models.CharField('코드설명', max_length=200, blank=True)
    code_order = models.IntegerField('정렬순서', default=0)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    insert_id = models.CharField('등록자', max_length=12, blank=True)
    yard_seq = models.CharField('구장순서', max_length=2, blank=True)

    class Meta:
        db_table = 'common_codevalue'
        verbose_name = '코드값'
        verbose_name_plural = '코드값'

    def __str__(self):
        return f'{self.group_id}/{self.subcode} - {self.code_name}'


class Setting(models.Model):
    """시스템 설정 (lf_setting)"""
    join_price = models.IntegerField('입단비', default=0)
    pk_price = models.IntegerField('PK비', default=0)
    insert_id = models.CharField('등록자', max_length=50, blank=True)
    insert_dt = models.DateTimeField('등록일')

    class Meta:
        db_table = 'common_setting'
        verbose_name = '시스템설정'
        verbose_name_plural = '시스템설정'

    def __str__(self):
        return f'입단비: {self.join_price} / PK비: {self.pk_price}'
