from django.utils import timezone
from .models import PointConfig, PointHistory


def add_point_history(member_id, member_name, app_gbn, app_point,
                      point_desc, order_no='', confirm_id='', insert_id=''):
    """포인트 내역 등록"""
    now = timezone.localtime()
    return PointHistory.objects.create(
        point_dt=now.strftime('%Y-%m-%d'),
        member_id=member_id,
        member_name=member_name,
        app_gbn=app_gbn,
        app_point=int(round(float(app_point))),
        point_desc=point_desc,
        order_no=str(order_no),
        confirm_id=confirm_id,
        insert_dt=now,
        insert_id=insert_id or member_id,
    )


def calculate_shop_point(settle_price):
    """쇼핑몰 구매 시 적립 포인트 계산"""
    try:
        p601 = PointConfig.objects.get(point_seq='601')
        p602 = PointConfig.objects.get(point_seq='602')
    except PointConfig.DoesNotExist:
        return 0

    # 결제금액이 limit_point 이상이면 602 규칙, 미만이면 601 규칙
    if settle_price >= p602.limit_point and p602.use_yn == 'Y':
        config = p602
    elif p601.use_yn == 'Y':
        config = p601
    else:
        return 0

    if config.save_gbn == 'PE':
        return int(round(settle_price * config.save_point / 100))
    else:
        return config.save_point
