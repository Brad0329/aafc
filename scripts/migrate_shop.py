"""
MSSQL → PostgreSQL 쇼핑몰 데이터 이관 스크립트
실행: python scripts/migrate_shop.py
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

import pyodbc
from django.utils import timezone
from apps.shop.models import (
    Category, Product, ProductOption, ProductOptionItem, ProductOptionStock,
    Order, OrderItem, OrderItemOption, OrderDelivery, ShopPaymentKCP,
)

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def safe_str(val):
    if val is None:
        return ''
    return str(val).strip()


def checkint(val):
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def checkfloat(val):
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def make_aware(dt):
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def migrate_category():
    """lf_shop_category → Category"""
    print('=== lf_shop_category → Category 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_category")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_category: {total}건')

    Category.objects.all().delete()
    print('기존 Category 데이터 삭제')

    cursor.execute("""
        SELECT cate_code, cate_name, cate_depth, cate_sort, cate_parent,
               cate_img, cate_isDisplay, del_ok, insert_dt, insert_id
        FROM lf_shop_category
        ORDER BY cate_code
    """)

    batch = []
    for row in cursor.fetchall():
        batch.append(Category(
            cate_code=checkint(row[0]),
            cate_name=safe_str(row[1]),
            cate_depth=checkint(row[2]),
            cate_sort=checkint(row[3]),
            cate_parent=checkint(row[4]),
            cate_img=safe_str(row[5]),
            cate_is_display=safe_str(row[6]) or 'Y',
            del_ok=safe_str(row[7]) or 'N',
            insert_dt=make_aware(row[8]) if row[8] else None,
            insert_id=safe_str(row[9]),
        ))

    Category.objects.bulk_create(batch)
    conn.close()
    pg_count = Category.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return pg_count


def migrate_product():
    """lf_shop_goods → Product"""
    print('\n=== lf_shop_goods → Product 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_goods")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_goods: {total}건')

    Product.objects.all().delete()
    print('기존 Product 데이터 삭제')

    # 유효한 cate_code 목록
    valid_cate = set(Category.objects.values_list('cate_code', flat=True))

    cursor.execute("""
        SELECT gd_code, cate_code, gd_name, gd_imgB, gd_imgM, gd_imgS,
               gd_desc, gd_desc_img, gd_product, gd_PlaceOfOrigin, gd_brand,
               gd_stock, gd_price, gd_marketPrice, gd_originalPrice, gd_PayPrice,
               gd_PayPoint, gd_point, gd_opionkind, gd_DeliveryKind,
               gd_deliveryFee, gd_DeliveryLimit, gd_readcnt,
               gd_display, gd_isSoldout, gd_type, gd_state, del_ok,
               gd_sort, order_number, local_code, sta_code,
               local_gubun, local_gubun2,
               gd_DeliveryPolicy, gd_ChangePolicy,
               insert_dt, insert_id
        FROM lf_shop_goods
        ORDER BY gd_code
    """)

    count = 0
    batch = []
    for row in cursor.fetchall():
        cate_code = checkint(row[1])
        batch.append(Product(
            gd_code=checkint(row[0]),
            category_id=cate_code if cate_code in valid_cate else None,
            gd_name=safe_str(row[2]),
            gd_img_b=safe_str(row[3]),
            gd_img_m=safe_str(row[4]),
            gd_img_s=safe_str(row[5]),
            gd_desc=safe_str(row[6]),
            gd_desc_img=safe_str(row[7]),
            gd_product=safe_str(row[8]),
            gd_place_of_origin=safe_str(row[9]),
            gd_brand=safe_str(row[10]),
            gd_stock=safe_str(row[11]),
            gd_price=checkint(row[12]),
            gd_market_price=checkint(row[13]),
            gd_original_price=checkint(row[14]),
            gd_pay_price=checkint(row[15]),
            gd_pay_point=checkint(row[16]),
            gd_point=checkint(row[17]),
            gd_option_kind=safe_str(row[18]),
            gd_delivery_kind=safe_str(row[19]) or '101',
            gd_delivery_fee=checkint(row[20]),
            gd_delivery_limit=checkint(row[21]),
            gd_readcnt=checkint(row[22]),
            gd_display=safe_str(row[23]) or 'Y',
            gd_is_soldout=safe_str(row[24]) or 'N',
            gd_type=safe_str(row[25]),
            gd_state=safe_str(row[26]),
            del_ok=safe_str(row[27]) or 'N',
            gd_sort=checkint(row[28]),
            order_number=safe_str(row[29]),
            local_code=safe_str(row[30]),
            sta_code=safe_str(row[31]),
            local_gubun=safe_str(row[32]),
            local_gubun2=safe_str(row[33]),
            gd_delivery_policy=safe_str(row[34]),
            gd_change_policy=safe_str(row[35]),
            insert_dt=make_aware(row[36]) if row[36] else None,
            insert_id=safe_str(row[37]),
        ))
        count += 1
        if len(batch) >= 100:
            Product.objects.bulk_create(batch)
            batch = []
            print(f'  {count}건 처리중...')

    if batch:
        Product.objects.bulk_create(batch)

    conn.close()
    pg_count = Product.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return pg_count


def migrate_product_option():
    """lf_shop_goods_option → ProductOption"""
    print('\n=== lf_shop_goods_option → ProductOption 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_goods_option")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_goods_option: {total}건')

    ProductOption.objects.all().delete()
    print('기존 ProductOption 데이터 삭제')

    valid_gd = set(Product.objects.values_list('gd_code', flat=True))

    # MSSQL idx → Django id 매핑용
    option_map = {}

    cursor.execute("""
        SELECT idx, goods_code, opt_name, opt_items,
               opt_isDisplay, opt_isRequire, opt_sort, del_ok,
               insert_id, insert_dt, org_idx
        FROM lf_shop_goods_option
        ORDER BY idx
    """)

    skip = 0
    for row in cursor.fetchall():
        ms_idx = checkint(row[0])
        goods_code = checkint(row[1])
        if goods_code not in valid_gd:
            skip += 1
            continue

        obj = ProductOption.objects.create(
            product_id=goods_code,
            opt_name=safe_str(row[2]),
            opt_items=safe_str(row[3]),
            opt_is_display=safe_str(row[4]) or 'T',
            opt_is_require=safe_str(row[5]) or 'T',
            opt_sort=checkint(row[6]),
            del_ok=safe_str(row[7]) or 'N',
            insert_id=safe_str(row[8]),
            insert_dt=make_aware(row[9]) if row[9] else None,
            org_idx=checkint(row[10]) if row[10] else None,
        )
        option_map[ms_idx] = obj.id

    conn.close()
    pg_count = ProductOption.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return option_map


def migrate_product_option_item(option_map):
    """lf_shop_goods_option_item → ProductOptionItem"""
    print('\n=== lf_shop_goods_option_item → ProductOptionItem 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_goods_option_item")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_goods_option_item: {total}건')

    ProductOptionItem.objects.all().delete()
    print('기존 ProductOptionItem 데이터 삭제')

    # MSSQL item idx → Django id 매핑용
    item_map = {}

    cursor.execute("""
        SELECT idx, opt_idx, opt_item, opt_price, opt_sort
        FROM lf_shop_goods_option_item
        ORDER BY idx
    """)

    skip = 0
    for row in cursor.fetchall():
        ms_idx = checkint(row[0])
        ms_opt_idx = checkint(row[1])
        django_opt_id = option_map.get(ms_opt_idx)
        if not django_opt_id:
            skip += 1
            continue

        obj = ProductOptionItem.objects.create(
            option_id=django_opt_id,
            opt_item=safe_str(row[2]),
            opt_price=checkint(row[3]),
            opt_sort=checkint(row[4]),
        )
        item_map[ms_idx] = obj.id

    conn.close()
    pg_count = ProductOptionItem.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return item_map


def migrate_product_option_stock():
    """lf_shop_goods_option_stock → ProductOptionStock"""
    print('\n=== lf_shop_goods_option_stock → ProductOptionStock 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_goods_option_stock")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_goods_option_stock: {total}건')

    ProductOptionStock.objects.all().delete()
    print('기존 ProductOptionStock 데이터 삭제')

    valid_gd = set(Product.objects.values_list('gd_code', flat=True))

    cursor.execute("""
        SELECT idx, goods_code, opt_item_idx1, opt_item_idx2, opt_stock
        FROM lf_shop_goods_option_stock
        ORDER BY idx
    """)

    batch = []
    skip = 0
    for row in cursor.fetchall():
        goods_code = checkint(row[1])
        if goods_code not in valid_gd:
            skip += 1
            continue

        batch.append(ProductOptionStock(
            product_id=goods_code,
            opt_item_idx1=checkint(row[2]),
            opt_item_idx2=checkint(row[3]),
            opt_stock=checkint(row[4]),
        ))
        if len(batch) >= 100:
            ProductOptionStock.objects.bulk_create(batch)
            batch = []

    if batch:
        ProductOptionStock.objects.bulk_create(batch)

    conn.close()
    pg_count = ProductOptionStock.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return pg_count


def migrate_order():
    """lf_shop_order → Order"""
    print('\n=== lf_shop_order → Order 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_order")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_order: {total}건')

    Order.objects.all().delete()
    print('기존 Order 데이터 삭제')

    # Member username 목록
    from apps.accounts.models import Member
    valid_members = set(Member.objects.values_list('username', flat=True))

    # MSSQL Uid → Django id 매핑용
    order_map = {}

    cursor.execute("""
        SELECT Uid, OrderNo, PersonUid, UserID, Payway, PayMethod, Pg,
               TotalPrice, TotalOrderPrice, TotalOptionPrice, TotalDeliveryFee,
               TotalUserDiscountPrice, TotalCouponDiscountPrice, UseCmoney,
               SettlePrice, OrgSettlePrice, PayCms, AddCmoney,
               OrdName, OrdTel, OrdMobile, OrdPost, OrdAddr, OrdAddrDetail, OrdEmail,
               RcvName, RcvTel, RcvMobile, RcvPost, RcvAddr, RcvAddrDetail,
               OrderMemo, AdminMemo, State, IsFinish,
               IsConfirm, IsDeliveryFinish, IsRefunded, IsCancel,
               child_id, MobileYn, RegDate, CancelDate, ConfirmDate
        FROM lf_shop_order
        ORDER BY Uid
    """)

    count = 0
    skip = 0
    seen_order_no = set()

    for row in cursor.fetchall():
        ms_uid = checkint(row[0])
        order_no = safe_str(row[1])
        person_uid = safe_str(row[2])

        # 중복 order_no 처리
        if order_no in seen_order_no:
            order_no = f'{order_no}_{ms_uid}'
        seen_order_no.add(order_no)

        member_id = person_uid if person_uid in valid_members else None

        obj = Order(
            order_no=order_no,
            member_id=member_id,
            user_id=safe_str(row[3]),
            payway=safe_str(row[4]),
            pay_method=safe_str(row[5]),
            pg=safe_str(row[6]),
            total_price=checkint(row[7]),
            total_order_price=checkint(row[8]),
            total_option_price=checkint(row[9]),
            total_delivery_fee=checkint(row[10]),
            total_user_discount=checkint(row[11]),
            total_coupon_discount=checkint(row[12]),
            use_cmoney=checkint(row[13]),
            settle_price=checkint(row[14]),
            org_settle_price=checkint(row[15]),
            pay_cms=checkfloat(row[16]),
            add_cmoney=checkint(row[17]),
            ord_name=safe_str(row[18]),
            ord_tel=safe_str(row[19]),
            ord_mobile=safe_str(row[20]),
            ord_post=safe_str(row[21]),
            ord_addr=safe_str(row[22]),
            ord_addr_detail=safe_str(row[23]),
            ord_email=safe_str(row[24]),
            rcv_name=safe_str(row[25]),
            rcv_tel=safe_str(row[26]),
            rcv_mobile=safe_str(row[27]),
            rcv_post=safe_str(row[28]),
            rcv_addr=safe_str(row[29]),
            rcv_addr_detail=safe_str(row[30]),
            order_memo=safe_str(row[31]),
            admin_memo=safe_str(row[32]),
            state=checkint(row[33]) or 100,
            is_finish=safe_str(row[34]) or 'F',
            is_confirm=safe_str(row[35]) or 'F',
            is_delivery_finish=safe_str(row[36]) or 'F',
            is_refunded=safe_str(row[37]) or 'F',
            is_cancel=safe_str(row[38]) or 'F',
            child_id=safe_str(row[39]),
            mobile_yn=safe_str(row[40]) or 'N',
            reg_date=make_aware(row[41]) if row[41] else None,
            cancel_date=make_aware(row[42]) if row[42] else None,
            confirm_date=make_aware(row[43]) if row[43] else None,
        )
        obj.save()
        order_map[ms_uid] = obj.id
        count += 1
        if count % 1000 == 0:
            print(f'  {count}건 처리중...')

    conn.close()
    pg_count = Order.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return order_map


def migrate_order_item(order_map):
    """lf_shop_order_info → OrderItem"""
    print('\n=== lf_shop_order_info → OrderItem 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_order_info")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_order_info: {total}건')

    OrderItem.objects.all().delete()
    print('기존 OrderItem 데이터 삭제')

    # MSSQL Uid → Django id 매핑
    item_map = {}

    cursor.execute("""
        SELECT Uid, OrderUid, GoodsUid, CateCode, GoodsType,
               GoodsCode, GoodsTitle, GoodsImg,
               Price, OriginalPrice, MarketPrice, OptionPrice,
               Ea, OptionKind, OptionTxt,
               UserDiscountPrice, CouponDiscountPrice, AddCmoney,
               Age, Sex
        FROM lf_shop_order_info
        ORDER BY Uid
    """)

    count = 0
    skip = 0
    for row in cursor.fetchall():
        ms_uid = checkint(row[0])
        ms_order_uid = checkint(row[1])
        django_order_id = order_map.get(ms_order_uid)
        if not django_order_id:
            skip += 1
            continue

        obj = OrderItem(
            order_id=django_order_id,
            goods_uid=checkint(row[2]),
            cate_code=checkint(row[3]),
            goods_type=safe_str(row[4]),
            goods_code=safe_str(row[5]),
            goods_title=safe_str(row[6])[:250],
            goods_img=safe_str(row[7]),
            price=checkint(row[8]),
            original_price=checkint(row[9]),
            market_price=checkint(row[10]),
            option_price=checkint(row[11]),
            ea=checkint(row[12]) or 1,
            option_kind=safe_str(row[13]),
            option_txt=safe_str(row[14]),
            user_discount_price=checkint(row[15]),
            coupon_discount_price=checkint(row[16]),
            add_cmoney=checkint(row[17]),
            age=safe_str(row[18]),
            sex=safe_str(row[19]),
        )
        obj.save()
        item_map[ms_uid] = obj.id
        count += 1
        if count % 2000 == 0:
            print(f'  {count}건 처리중...')

    conn.close()
    pg_count = OrderItem.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return item_map


def migrate_order_item_option(item_map):
    """lf_shop_order_option → OrderItemOption"""
    print('\n=== lf_shop_order_option → OrderItemOption 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_order_option")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_order_option: {total}건')

    OrderItemOption.objects.all().delete()
    print('기존 OrderItemOption 데이터 삭제')

    cursor.execute("""
        SELECT Uid, OrderInfoUid, Title, Item, Price, Sort
        FROM lf_shop_order_option
        ORDER BY Uid
    """)

    count = 0
    skip = 0
    batch = []
    for row in cursor.fetchall():
        ms_info_uid = checkint(row[1])
        django_item_id = item_map.get(ms_info_uid)
        if not django_item_id:
            skip += 1
            continue

        batch.append(OrderItemOption(
            order_item_id=django_item_id,
            title=safe_str(row[2]),
            item=safe_str(row[3]),
            price=checkint(row[4]),
            sort=checkint(row[5]),
        ))
        count += 1
        if len(batch) >= 100:
            OrderItemOption.objects.bulk_create(batch)
            batch = []
            if count % 2000 == 0:
                print(f'  {count}건 처리중...')

    if batch:
        OrderItemOption.objects.bulk_create(batch)

    conn.close()
    pg_count = OrderItemOption.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return pg_count


def migrate_order_delivery(order_map):
    """lf_shop_order_delivery → OrderDelivery"""
    print('\n=== lf_shop_order_delivery → OrderDelivery 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_order_delivery")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_order_delivery: {total}건')

    OrderDelivery.objects.all().delete()
    print('기존 OrderDelivery 데이터 삭제')

    cursor.execute("""
        SELECT Uid, OrderUid, DeliveryPolicy, DeliveryMethod,
               DeliveryFee, DeliveryLimit, RealDeliveryFee,
               IsDelivery, DeliveryUid, DeliveryName, DeliveryNo, DeliveryDate
        FROM lf_shop_order_delivery
        ORDER BY Uid
    """)

    count = 0
    skip = 0
    batch = []
    for row in cursor.fetchall():
        ms_order_uid = checkint(row[1])
        django_order_id = order_map.get(ms_order_uid)
        if not django_order_id:
            skip += 1
            continue

        batch.append(OrderDelivery(
            order_id=django_order_id,
            delivery_policy=safe_str(row[2]),
            delivery_method=safe_str(row[3]),
            delivery_fee=checkint(row[4]),
            delivery_limit=checkint(row[5]),
            real_delivery_fee=checkint(row[6]),
            is_delivery=safe_str(row[7]) or 'N',
            delivery_uid=safe_str(row[8]),
            delivery_name=safe_str(row[9]),
            delivery_no=safe_str(row[10]),
            delivery_date=make_aware(row[11]) if row[11] else None,
        ))
        count += 1
        if len(batch) >= 100:
            OrderDelivery.objects.bulk_create(batch)
            batch = []
            if count % 2000 == 0:
                print(f'  {count}건 처리중...')

    if batch:
        OrderDelivery.objects.bulk_create(batch)

    conn.close()
    pg_count = OrderDelivery.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return pg_count


def migrate_shop_payment_kcp(order_map):
    """lf_shop_pay_kcp → ShopPaymentKCP"""
    print('\n=== lf_shop_pay_kcp → ShopPaymentKCP 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_shop_pay_kcp")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_shop_pay_kcp: {total}건')

    ShopPaymentKCP.objects.all().delete()
    print('기존 ShopPaymentKCP 데이터 삭제')

    # order_no → Order id 매핑
    order_no_map = dict(Order.objects.values_list('order_no', 'id'))

    cursor.execute("""
        SELECT Uid, UsePayMethod, ResCd, ResMsg, Tno, Amount,
               CardCd, CardName, AppTime, AppNo, Noinf, Quota,
               BankName, Depositor, Account, CashYn, CashAuthno, NotiId
        FROM lf_shop_pay_kcp
        ORDER BY Uid
    """)

    count = 0
    batch = []
    for row in cursor.fetchall():
        ms_uid = checkint(row[0])

        batch.append(ShopPaymentKCP(
            use_pay_method=safe_str(row[1]),
            res_cd=safe_str(row[2]),
            res_msg=safe_str(row[3]),
            tno=safe_str(row[4]),
            amount=checkint(row[5]),
            card_cd=safe_str(row[6]),
            card_name=safe_str(row[7]),
            app_time=safe_str(row[8]),
            app_no=safe_str(row[9]),
            noinf=safe_str(row[10]),
            quota=safe_str(row[11]),
            bank_name=safe_str(row[12]),
            depositor=safe_str(row[13]),
            account=safe_str(row[14]),
            cash_yn=safe_str(row[15]),
            cash_authno=safe_str(row[16]),
            noti_id=safe_str(row[17]),
        ))
        count += 1
        if len(batch) >= 100:
            ShopPaymentKCP.objects.bulk_create(batch)
            batch = []
            if count % 2000 == 0:
                print(f'  {count}건 처리중...')

    if batch:
        ShopPaymentKCP.objects.bulk_create(batch)

    conn.close()
    pg_count = ShopPaymentKCP.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return pg_count


if __name__ == '__main__':
    print('쇼핑몰 데이터 마이그레이션 시작\n')

    migrate_category()
    migrate_product()
    option_map = migrate_product_option()
    migrate_product_option_item(option_map)
    migrate_product_option_stock()
    order_map = migrate_order()
    item_map = migrate_order_item(order_map)
    migrate_order_item_option(item_map)
    migrate_order_delivery(order_map)
    migrate_shop_payment_kcp(order_map)

    print('\n=== 최종 건수 확인 ===')
    print(f'Category: {Category.objects.count()}')
    print(f'Product: {Product.objects.count()}')
    print(f'ProductOption: {ProductOption.objects.count()}')
    print(f'ProductOptionItem: {ProductOptionItem.objects.count()}')
    print(f'ProductOptionStock: {ProductOptionStock.objects.count()}')
    print(f'Order: {Order.objects.count()}')
    print(f'OrderItem: {OrderItem.objects.count()}')
    print(f'OrderItemOption: {OrderItemOption.objects.count()}')
    print(f'OrderDelivery: {OrderDelivery.objects.count()}')
    print(f'ShopPaymentKCP: {ShopPaymentKCP.objects.count()}')
    print('\n쇼핑몰 데이터 마이그레이션 완료!')
