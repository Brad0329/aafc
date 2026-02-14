from django.conf import settings
from django.db import models


class Category(models.Model):
    """상품 카테고리 (lf_shop_category)"""
    cate_code = models.IntegerField('카테고리코드', unique=True)
    cate_name = models.CharField('카테고리명', max_length=100)
    cate_depth = models.IntegerField('카테고리 깊이', default=1)
    cate_sort = models.IntegerField('정렬순서', default=0)
    cate_parent = models.IntegerField('부모 카테고리코드', default=0)
    cate_img = models.CharField('카테고리 이미지', max_length=300, blank=True)
    cate_is_display = models.CharField('노출여부', max_length=1, default='Y')
    del_ok = models.CharField('삭제여부', max_length=1, default='N')
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    insert_id = models.CharField('등록자', max_length=20, blank=True)

    class Meta:
        db_table = 'shop_category'
        verbose_name = '상품 카테고리'
        verbose_name_plural = '상품 카테고리'
        ordering = ['cate_sort', 'cate_code']

    def __str__(self):
        return self.cate_name


class Product(models.Model):
    """상품 (lf_shop_goods)"""
    OPTION_KIND_CHOICES = [
        ('', '옵션없음'),
        ('100', '일반옵션'),
        ('200', '재고/가격옵션'),
    ]
    DELIVERY_KIND_CHOICES = [
        ('101', '무료배송'),
        ('102', '유료배송'),
    ]
    SOLDOUT_CHOICES = [
        ('N', '판매중'),
        ('Y', '품절'),
        ('S', '출시예정'),
    ]

    gd_code = models.IntegerField('상품코드', unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='카테고리',
        to_field='cate_code', db_column='cate_code',
    )
    gd_name = models.CharField('상품명', max_length=250)
    gd_img_b = models.CharField('대이미지', max_length=300, blank=True)
    gd_img_m = models.CharField('중이미지', max_length=300, blank=True)
    gd_img_s = models.CharField('소이미지', max_length=300, blank=True)
    gd_desc = models.TextField('상품설명', blank=True)
    gd_desc_img = models.CharField('설명이미지', max_length=300, blank=True)
    gd_product = models.CharField('제조사', max_length=100, blank=True)
    gd_place_of_origin = models.CharField('원산지', max_length=100, blank=True)
    gd_brand = models.CharField('브랜드', max_length=100, blank=True)
    gd_stock = models.CharField('재고수량', max_length=5, blank=True)
    gd_price = models.IntegerField('판매가격', default=0)
    gd_market_price = models.IntegerField('시장가격', default=0)
    gd_original_price = models.IntegerField('원가', default=0)
    gd_pay_price = models.IntegerField('결제가격', default=0)
    gd_pay_point = models.IntegerField('결제포인트', default=0)
    gd_point = models.IntegerField('적립포인트', default=0)
    gd_option_kind = models.CharField('옵션종류', max_length=3, blank=True, choices=OPTION_KIND_CHOICES)
    gd_delivery_kind = models.CharField('배송종류', max_length=3, default='101', choices=DELIVERY_KIND_CHOICES)
    gd_delivery_fee = models.IntegerField('배송비', default=0)
    gd_delivery_limit = models.IntegerField('무료배송기준금액', default=0)
    gd_readcnt = models.IntegerField('조회수', default=0)
    gd_display = models.CharField('노출여부', max_length=1, default='Y')
    gd_is_soldout = models.CharField('품절여부', max_length=1, default='N', choices=SOLDOUT_CHOICES)
    gd_type = models.CharField('상품타입', max_length=5, blank=True)
    gd_state = models.CharField('상품상태', max_length=20, blank=True)
    del_ok = models.CharField('삭제여부', max_length=1, default='N')
    gd_sort = models.IntegerField('정렬순서', default=0)
    order_number = models.CharField('주문번호', max_length=10, blank=True)
    local_code = models.CharField('권역코드', max_length=10, blank=True)
    sta_code = models.CharField('구장코드', max_length=10, blank=True)
    local_gubun = models.CharField('지역구분', max_length=5, blank=True)
    local_gubun2 = models.CharField('지역구분2', max_length=5, blank=True)
    gd_delivery_policy = models.TextField('배송정책', blank=True)
    gd_change_policy = models.TextField('반품/교환정책', blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    insert_id = models.CharField('등록자', max_length=20, blank=True)

    class Meta:
        db_table = 'shop_product'
        verbose_name = '상품'
        verbose_name_plural = '상품'
        ordering = ['gd_sort', '-gd_code']

    def __str__(self):
        return self.gd_name

    def get_image_url(self):
        if self.gd_img_b:
            return f'/fcdata/shop_goods/{self.gd_img_b}'
        return ''


class ProductOption(models.Model):
    """상품 옵션 그룹 (lf_shop_goods_option)"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='options', verbose_name='상품',
        to_field='gd_code', db_column='goods_code',
    )
    opt_name = models.CharField('옵션명', max_length=100)
    opt_items = models.TextField('옵션항목(콤마구분)', blank=True)
    opt_is_display = models.CharField('노출여부', max_length=1, default='T')
    opt_is_require = models.CharField('필수여부', max_length=1, default='T')
    opt_sort = models.IntegerField('정렬순서', default=0)
    del_ok = models.CharField('삭제여부', max_length=1, default='N')
    insert_id = models.CharField('등록자', max_length=20, blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    org_idx = models.IntegerField('원본ID', null=True, blank=True)

    class Meta:
        db_table = 'shop_productoption'
        verbose_name = '상품옵션'
        verbose_name_plural = '상품옵션'
        ordering = ['opt_sort']

    def __str__(self):
        return f'{self.product_id} - {self.opt_name}'


class ProductOptionItem(models.Model):
    """상품 옵션 항목 (lf_shop_goods_option_item)"""
    option = models.ForeignKey(
        ProductOption, on_delete=models.CASCADE,
        related_name='items', verbose_name='옵션그룹',
        db_column='opt_idx',
    )
    opt_item = models.CharField('옵션항목명', max_length=200)
    opt_price = models.IntegerField('추가금액', default=0)
    opt_sort = models.IntegerField('정렬순서', default=0)

    class Meta:
        db_table = 'shop_productoptionitem'
        verbose_name = '옵션항목'
        verbose_name_plural = '옵션항목'
        ordering = ['opt_sort']

    def __str__(self):
        return self.opt_item


class ProductOptionStock(models.Model):
    """상품 옵션별 재고 (lf_shop_goods_option_stock)"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='option_stocks', verbose_name='상품',
        to_field='gd_code', db_column='goods_code',
    )
    opt_item_idx1 = models.IntegerField('옵션항목1 ID', default=0)
    opt_item_idx2 = models.IntegerField('옵션항목2 ID', default=0)
    opt_stock = models.IntegerField('재고수량', default=0)

    class Meta:
        db_table = 'shop_productoptionstock'
        verbose_name = '옵션재고'
        verbose_name_plural = '옵션재고'

    def __str__(self):
        return f'상품{self.product_id} 재고:{self.opt_stock}'


class Cart(models.Model):
    """장바구니 (lf_shop_cart)"""
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart_items', verbose_name='회원',
        to_field='username', db_column='member_num',
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='cart_items', verbose_name='상품',
        to_field='gd_code', db_column='gd_code',
    )
    ea = models.IntegerField('수량', default=1)
    option_kind = models.CharField('옵션종류', max_length=3, blank=True)
    option_txt = models.TextField('서술형옵션', blank=True)
    insert_dt = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'shop_cart'
        verbose_name = '장바구니'
        verbose_name_plural = '장바구니'
        ordering = ['-id']

    def __str__(self):
        return f'{self.member_id} - {self.product_id} x{self.ea}'


class CartOption(models.Model):
    """장바구니 옵션 (lf_shop_cart_option)"""
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE,
        related_name='options', verbose_name='장바구니',
    )
    option_title = models.CharField('옵션명', max_length=100)
    option_item_uid = models.IntegerField('옵션항목ID', default=0)
    option_item = models.CharField('옵션항목명', max_length=100)
    option_price = models.IntegerField('옵션추가금액', default=0)
    sort = models.IntegerField('정렬순서', default=0)

    class Meta:
        db_table = 'shop_cartoption'
        verbose_name = '장바구니옵션'
        verbose_name_plural = '장바구니옵션'
        ordering = ['sort']

    def __str__(self):
        return f'{self.option_title}: {self.option_item}'


class Order(models.Model):
    """주문 (lf_shop_order)"""
    ORDER_STATES = [
        (100, '신규주문'),
        (200, '배송준비(입금확인)'),
        (301, '배송중'),
        (302, '배송완료'),
        (402, '취소'),
    ]
    PAYWAY_CHOICES = [
        ('CARD', '신용카드'),
        ('BANK', '계좌이체'),
        ('ZEROPAY', '제로페이'),
    ]

    order_no = models.CharField('주문번호', max_length=50, unique=True)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shop_orders', verbose_name='회원',
        to_field='username', db_column='person_uid',
    )
    user_id = models.CharField('회원아이디', max_length=30, blank=True)
    child_id = models.CharField('자녀아이디', max_length=25, blank=True)
    payway = models.CharField('결제방법코드', max_length=10, blank=True, choices=PAYWAY_CHOICES)
    pay_method = models.CharField('결제수단상세', max_length=50, blank=True)
    pg = models.CharField('PG사', max_length=20, blank=True)
    total_price = models.IntegerField('총상품금액', default=0)
    total_order_price = models.IntegerField('총주문금액', default=0)
    total_option_price = models.IntegerField('총옵션금액', default=0)
    total_delivery_fee = models.IntegerField('총배송비', default=0)
    total_user_discount = models.IntegerField('회원할인', default=0)
    total_coupon_discount = models.IntegerField('쿠폰할인', default=0)
    use_cmoney = models.IntegerField('사용적립금', default=0)
    settle_price = models.IntegerField('최종결제금액', default=0)
    org_settle_price = models.IntegerField('원결제금액', default=0)
    pay_cms = models.FloatField('수수료율', default=0)
    add_cmoney = models.IntegerField('적립금', default=0)

    # 주문자 정보
    ord_name = models.CharField('주문자명', max_length=60, blank=True)
    ord_tel = models.CharField('주문자전화', max_length=30, blank=True)
    ord_mobile = models.CharField('주문자휴대폰', max_length=30, blank=True)
    ord_post = models.CharField('주문자우편번호', max_length=7, blank=True)
    ord_addr = models.CharField('주문자주소', max_length=200, blank=True)
    ord_addr_detail = models.CharField('주문자상세주소', max_length=200, blank=True)
    ord_email = models.CharField('주문자이메일', max_length=100, blank=True)

    # 수령인 정보
    rcv_name = models.CharField('수령인명', max_length=60, blank=True)
    rcv_tel = models.CharField('수령인전화', max_length=30, blank=True)
    rcv_mobile = models.CharField('수령인휴대폰', max_length=30, blank=True)
    rcv_post = models.CharField('수령인우편번호', max_length=7, blank=True)
    rcv_addr = models.CharField('수령인주소', max_length=200, blank=True)
    rcv_addr_detail = models.CharField('수령인상세주소', max_length=200, blank=True)
    rcv_email = models.CharField('수령인이메일', max_length=100, blank=True)

    order_memo = models.TextField('주문메모', blank=True)
    admin_memo = models.TextField('관리자메모', blank=True)
    state = models.IntegerField('주문상태', default=100, choices=ORDER_STATES)
    is_finish = models.CharField('결제완료', max_length=1, default='F')
    is_confirm = models.CharField('확인여부', max_length=1, default='F')
    is_delivery_finish = models.CharField('배송완료', max_length=1, default='F')
    is_refunded = models.CharField('환불여부', max_length=1, default='F')
    is_cancel = models.CharField('취소여부', max_length=1, default='F')
    mobile_yn = models.CharField('모바일여부', max_length=1, default='N')
    reg_date = models.DateTimeField('주문일시', null=True, blank=True)
    cancel_date = models.DateTimeField('취소일시', null=True, blank=True)
    confirm_date = models.DateTimeField('확인일시', null=True, blank=True)

    class Meta:
        db_table = 'shop_order'
        verbose_name = '주문'
        verbose_name_plural = '주문'
        ordering = ['-id']

    def __str__(self):
        return f'{self.order_no} ({self.get_state_display()})'


class OrderItem(models.Model):
    """주문 상품 (lf_shop_order_info)"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='주문',
    )
    goods_uid = models.IntegerField('상품코드', default=0)
    cate_code = models.IntegerField('카테고리코드', default=0)
    goods_type = models.CharField('상품타입', max_length=5, blank=True)
    goods_code = models.CharField('상품코드문자', max_length=20, blank=True)
    goods_title = models.CharField('상품명', max_length=250)
    goods_img = models.CharField('상품이미지', max_length=300, blank=True)
    price = models.IntegerField('상품단가', default=0)
    original_price = models.IntegerField('원가', default=0)
    market_price = models.IntegerField('시장가', default=0)
    option_price = models.IntegerField('옵션가격합계', default=0)
    ea = models.IntegerField('수량', default=1)
    option_kind = models.CharField('옵션종류', max_length=3, blank=True)
    option_txt = models.TextField('옵션텍스트', blank=True)
    user_discount_price = models.IntegerField('회원할인', default=0)
    coupon_discount_price = models.IntegerField('쿠폰할인', default=0)
    add_cmoney = models.IntegerField('적립금', default=0)
    age = models.CharField('나이', max_length=20, blank=True)
    sex = models.CharField('성별', max_length=20, blank=True)

    class Meta:
        db_table = 'shop_orderitem'
        verbose_name = '주문상품'
        verbose_name_plural = '주문상품'

    def __str__(self):
        return f'주문#{self.order_id} {self.goods_title} x{self.ea}'

    @property
    def subtotal(self):
        return (self.price + self.option_price) * self.ea


class OrderItemOption(models.Model):
    """주문 상품 옵션 (lf_shop_order_option)"""
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE,
        related_name='options', verbose_name='주문상품',
    )
    title = models.CharField('옵션명', max_length=100)
    item = models.CharField('옵션항목', max_length=200)
    price = models.IntegerField('옵션가격', default=0)
    sort = models.IntegerField('정렬순서', default=0)

    class Meta:
        db_table = 'shop_orderitemoption'
        verbose_name = '주문상품옵션'
        verbose_name_plural = '주문상품옵션'
        ordering = ['sort']

    def __str__(self):
        return f'{self.title}: {self.item}'


class OrderDelivery(models.Model):
    """주문 배송 정보 (lf_shop_order_delivery)"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='deliveries', verbose_name='주문',
    )
    delivery_policy = models.CharField('배송정책', max_length=10, blank=True)
    delivery_method = models.CharField('배송방법', max_length=10, blank=True)
    delivery_fee = models.IntegerField('배송비', default=0)
    delivery_limit = models.IntegerField('무료배송기준', default=0)
    real_delivery_fee = models.IntegerField('실배송비', default=0)
    is_delivery = models.CharField('배송여부', max_length=1, default='N')
    delivery_uid = models.CharField('배송UID', max_length=50, blank=True)
    delivery_name = models.CharField('택배사', max_length=50, blank=True)
    delivery_no = models.CharField('송장번호', max_length=50, blank=True)
    delivery_date = models.DateTimeField('배송일', null=True, blank=True)

    class Meta:
        db_table = 'shop_orderdelivery'
        verbose_name = '배송정보'
        verbose_name_plural = '배송정보'

    def __str__(self):
        return f'주문#{self.order_id} {self.delivery_name} {self.delivery_no or "미입력"}'


class ShopPaymentKCP(models.Model):
    """쇼핑몰 KCP 결제 로그 (lf_shop_pay_kcp)"""
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kcp_payments', verbose_name='주문',
    )
    use_pay_method = models.CharField('결제수단코드', max_length=20, blank=True)
    res_cd = models.CharField('응답코드', max_length=10, blank=True)
    res_msg = models.CharField('응답메시지', max_length=200, blank=True)
    tno = models.CharField('거래번호', max_length=100, blank=True)
    amount = models.IntegerField('결제금액', default=0)
    card_cd = models.CharField('카드코드', max_length=10, blank=True)
    card_name = models.CharField('카드명', max_length=50, blank=True)
    app_time = models.CharField('승인시간', max_length=20, blank=True)
    app_no = models.CharField('승인번호', max_length=20, blank=True)
    noinf = models.CharField('무이자여부', max_length=5, blank=True)
    quota = models.CharField('할부개월', max_length=3, blank=True)
    bank_name = models.CharField('은행명', max_length=20, blank=True)
    depositor = models.CharField('입금자명', max_length=50, blank=True)
    account = models.CharField('계좌번호', max_length=50, blank=True)
    cash_yn = models.CharField('현금영수증', max_length=1, blank=True)
    cash_authno = models.CharField('현금영수증번호', max_length=50, blank=True)
    noti_id = models.CharField('알림ID', max_length=50, blank=True)
    member_num = models.CharField('회원아이디', max_length=30, blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'shop_shoppaymentkcp'
        verbose_name = '쇼핑몰KCP결제'
        verbose_name_plural = '쇼핑몰KCP결제'
        ordering = ['-id']

    def __str__(self):
        return f'#{self.id} {self.tno} {self.amount}원'
