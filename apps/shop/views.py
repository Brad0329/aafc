import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.models import MemberChild
from .models import (
    Category, Product, ProductOption, ProductOptionItem, ProductOptionStock,
    Cart, CartOption, Order, OrderItem, OrderItemOption, OrderDelivery,
    ShopPaymentKCP,
)

SHOP_MENU = [
    {'id': 'shop_goods', 'title': '상품리스트', 'url_name': 'shop:goods_list'},
    {'id': 'shop_basket', 'title': '장바구니', 'url_name': 'shop:cart'},
    {'id': 'shop_lookup', 'title': '주문/배송조회', 'url_name': 'shop:order_list'},
]


# ── 상품 카탈로그 ──

def goods_list(request):
    """상품 목록"""
    selcate = request.GET.get('selcate_code', '')

    categories = Category.objects.filter(del_ok='N', cate_is_display='Y')
    products = Product.objects.filter(del_ok='N', gd_display='Y')

    if selcate:
        products = products.filter(category__cate_code=int(selcate))

    context = {
        'shop_menu': SHOP_MENU,
        'current_menu': 'shop_goods',
        'categories': categories,
        'products': products,
        'selcate': selcate,
    }
    return render(request, 'shop/goods_list.html', context)


def goods_view(request, gd_code):
    """상품 상세"""
    product = get_object_or_404(Product, gd_code=gd_code, del_ok='N', gd_display='Y')

    # 조회수 증가
    Product.objects.filter(pk=product.pk).update(gd_readcnt=product.gd_readcnt + 1)

    # 옵션 로드
    options = ProductOption.objects.filter(
        product=product, del_ok='N'
    ).prefetch_related('items').order_by('opt_sort')

    context = {
        'shop_menu': SHOP_MENU,
        'current_menu': 'shop_goods',
        'product': product,
        'options': options,
    }
    return render(request, 'shop/goods_view.html', context)


def ajax_option_stock(request):
    """옵션 조합별 재고 확인 (AJAX)"""
    goods_code = request.GET.get('goods_code', 0)
    opt_item_idx1 = request.GET.get('opt_item_idx1', 0)
    opt_item_idx2 = request.GET.get('opt_item_idx2', 0)

    try:
        stock = ProductOptionStock.objects.get(
            product__gd_code=int(goods_code),
            opt_item_idx1=int(opt_item_idx1),
            opt_item_idx2=int(opt_item_idx2),
        )
        return JsonResponse({'stock': stock.opt_stock})
    except ProductOptionStock.DoesNotExist:
        return JsonResponse({'stock': 0})


# ── 장바구니 ──

@login_required
def cart_view(request):
    """장바구니 목록"""
    cart_items = Cart.objects.filter(
        member=request.user
    ).select_related('product', 'product__category').prefetch_related('options')

    total_price = 0
    total_delivery = 0
    items_data = []
    for item in cart_items:
        option_price = sum(opt.option_price for opt in item.options.all())
        item_total = (item.product.gd_price + option_price) * item.ea
        total_price += item_total

        # 배송비 계산
        delivery_fee = 0
        if item.product.gd_delivery_kind == '102':
            delivery_fee = item.product.gd_delivery_fee
            if item.product.gd_delivery_limit > 0 and item_total >= item.product.gd_delivery_limit:
                delivery_fee = 0
        total_delivery += delivery_fee

        items_data.append({
            'cart': item,
            'option_price': option_price,
            'item_total': item_total,
            'delivery_fee': delivery_fee,
        })

    context = {
        'shop_menu': SHOP_MENU,
        'current_menu': 'shop_basket',
        'items_data': items_data,
        'total_price': total_price,
        'total_delivery': total_delivery,
        'grand_total': total_price + total_delivery,
    }
    return render(request, 'shop/cart.html', context)


@login_required
def cart_add(request):
    """장바구니 추가 (POST)"""
    if request.method != 'POST':
        return redirect('shop:goods_list')

    gd_code = int(request.POST.get('gd_code', 0))
    ea = int(request.POST.get('ea', 1))
    option_kind = request.POST.get('option_kind', '')

    product = get_object_or_404(Product, gd_code=gd_code, del_ok='N')

    cart_item = Cart.objects.create(
        member=request.user,
        product=product,
        ea=ea,
        option_kind=option_kind,
    )

    # 옵션 저장
    option_count = int(request.POST.get('option_count', 0))
    for i in range(option_count):
        opt_title = request.POST.get(f'opt_title_{i}', '')
        opt_item_uid = int(request.POST.get(f'opt_item_uid_{i}', 0))
        opt_item = request.POST.get(f'opt_item_{i}', '')
        opt_price = int(request.POST.get(f'opt_price_{i}', 0))
        if opt_title and opt_item:
            CartOption.objects.create(
                cart=cart_item,
                option_title=opt_title,
                option_item_uid=opt_item_uid,
                option_item=opt_item,
                option_price=opt_price,
                sort=i,
            )

    # 바로구매인 경우
    if request.POST.get('buy_now') == 'Y':
        request.session['order_cart_ids'] = [cart_item.id]
        return redirect('shop:order_form')

    return redirect('shop:cart')


@login_required
def cart_delete(request):
    """장바구니 삭제 (POST)"""
    if request.method != 'POST':
        return redirect('shop:cart')

    cart_ids = request.POST.getlist('cart_ids')
    if cart_ids:
        Cart.objects.filter(id__in=cart_ids, member=request.user).delete()

    return redirect('shop:cart')


# ── 주문/결제 ──

@login_required
def order_form(request):
    """주문서 작성"""
    if request.method == 'POST':
        # 장바구니에서 선택한 항목
        cart_ids = request.POST.getlist('cart_ids')
        if not cart_ids:
            return redirect('shop:cart')
        request.session['order_cart_ids'] = [int(x) for x in cart_ids]

    cart_ids = request.session.get('order_cart_ids', [])
    if not cart_ids:
        return redirect('shop:cart')

    cart_items = Cart.objects.filter(
        id__in=cart_ids, member=request.user
    ).select_related('product', 'product__category').prefetch_related('options')

    if not cart_items.exists():
        return redirect('shop:cart')

    # 금액 계산
    total_price = 0
    total_delivery = 0
    items_data = []
    for item in cart_items:
        option_price = sum(opt.option_price for opt in item.options.all())
        item_total = (item.product.gd_price + option_price) * item.ea
        total_price += item_total

        delivery_fee = 0
        if item.product.gd_delivery_kind == '102':
            delivery_fee = item.product.gd_delivery_fee
            if item.product.gd_delivery_limit > 0 and item_total >= item.product.gd_delivery_limit:
                delivery_fee = 0
        total_delivery += delivery_fee

        items_data.append({
            'cart': item,
            'option_price': option_price,
            'item_total': item_total,
            'delivery_fee': delivery_fee,
        })

    settle_price = total_price + total_delivery

    # 자녀 목록
    children = MemberChild.objects.filter(parent=request.user, status='N')

    context = {
        'shop_menu': SHOP_MENU,
        'current_menu': 'shop_goods',
        'items_data': items_data,
        'total_price': total_price,
        'total_delivery': total_delivery,
        'settle_price': settle_price,
        'children': children,
        'user': request.user,
    }
    return render(request, 'shop/order_form.html', context)


@login_required
def order_create(request):
    """주문 생성 (AJAX POST)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST만 허용'}, status=405)

    cart_ids = request.session.get('order_cart_ids', [])
    if not cart_ids:
        return JsonResponse({'error': '주문할 상품이 없습니다.'}, status=400)

    cart_items = list(Cart.objects.filter(
        id__in=cart_ids, member=request.user
    ).select_related('product').prefetch_related('options'))

    if not cart_items:
        return JsonResponse({'error': '장바구니가 비어있습니다.'}, status=400)

    payway = request.POST.get('payway', 'CARD')
    child_id = request.POST.get('child_id', '')

    # 주문자 정보
    ord_name = request.POST.get('ord_name', '')
    ord_tel = request.POST.get('ord_tel', '')
    ord_mobile = request.POST.get('ord_mobile', '')
    ord_email = request.POST.get('ord_email', '')
    ord_post = request.POST.get('ord_post', '')
    ord_addr = request.POST.get('ord_addr', '')
    ord_addr_detail = request.POST.get('ord_addr_detail', '')

    # 수령인 정보
    rcv_name = request.POST.get('rcv_name', '')
    rcv_tel = request.POST.get('rcv_tel', '')
    rcv_mobile = request.POST.get('rcv_mobile', '')
    rcv_post = request.POST.get('rcv_post', '')
    rcv_addr = request.POST.get('rcv_addr', '')
    rcv_addr_detail = request.POST.get('rcv_addr_detail', '')

    order_memo = request.POST.get('order_memo', '')

    try:
        with transaction.atomic():
            now = timezone.localtime()
            order_no = now.strftime('%y%m%d%H%M%S') + str(now.microsecond)[:4]

            # 금액 계산
            total_price = 0
            total_option_price = 0
            total_delivery = 0
            first_goods_name = cart_items[0].product.gd_name

            for item in cart_items:
                opt_price = sum(opt.option_price for opt in item.options.all())
                total_price += item.product.gd_price * item.ea
                total_option_price += opt_price * item.ea

                if item.product.gd_delivery_kind == '102':
                    item_total = (item.product.gd_price + opt_price) * item.ea
                    fee = item.product.gd_delivery_fee
                    if item.product.gd_delivery_limit > 0 and item_total >= item.product.gd_delivery_limit:
                        fee = 0
                    total_delivery += fee

            settle_price = total_price + total_option_price + total_delivery

            pay_method_map = {'CARD': '신용카드', 'BANK': '계좌이체', 'ZEROPAY': '제로페이'}

            order = Order.objects.create(
                order_no=order_no,
                member=request.user,
                user_id=request.user.username,
                child_id=child_id,
                payway=payway,
                pay_method=pay_method_map.get(payway, ''),
                pg='KCP',
                total_price=total_price,
                total_order_price=total_price + total_option_price,
                total_option_price=total_option_price,
                total_delivery_fee=total_delivery,
                settle_price=settle_price,
                org_settle_price=settle_price,
                ord_name=ord_name,
                ord_tel=ord_tel,
                ord_mobile=ord_mobile,
                ord_email=ord_email,
                ord_post=ord_post,
                ord_addr=ord_addr,
                ord_addr_detail=ord_addr_detail,
                rcv_name=rcv_name,
                rcv_tel=rcv_tel,
                rcv_mobile=rcv_mobile,
                rcv_post=rcv_post,
                rcv_addr=rcv_addr,
                rcv_addr_detail=rcv_addr_detail,
                order_memo=order_memo,
                state=200,
                is_finish='T',
                confirm_date=now,
                reg_date=now,
            )

            # 주문 상품 생성
            for item in cart_items:
                opt_price = sum(opt.option_price for opt in item.options.all())
                option_txt_parts = [f'{o.option_title}:{o.option_item}' for o in item.options.all()]

                order_item = OrderItem.objects.create(
                    order=order,
                    goods_uid=item.product.gd_code,
                    cate_code=item.product.category_id or 0,
                    goods_type=item.product.gd_type,
                    goods_code=str(item.product.gd_code),
                    goods_title=item.product.gd_name,
                    goods_img=item.product.gd_img_s or item.product.gd_img_m or item.product.gd_img_b,
                    price=item.product.gd_price,
                    original_price=item.product.gd_original_price,
                    market_price=item.product.gd_market_price,
                    option_price=opt_price,
                    ea=item.ea,
                    option_kind=item.option_kind,
                    option_txt=' / '.join(option_txt_parts),
                )

                # 주문 상품 옵션
                for idx, opt in enumerate(item.options.all()):
                    OrderItemOption.objects.create(
                        order_item=order_item,
                        title=opt.option_title,
                        item=opt.option_item,
                        price=opt.option_price,
                        sort=idx,
                    )

                # 배송 정보
                delivery_fee = 0
                if item.product.gd_delivery_kind == '102':
                    item_total = (item.product.gd_price + opt_price) * item.ea
                    delivery_fee = item.product.gd_delivery_fee
                    if item.product.gd_delivery_limit > 0 and item_total >= item.product.gd_delivery_limit:
                        delivery_fee = 0

                OrderDelivery.objects.create(
                    order=order,
                    delivery_policy=item.product.gd_delivery_kind,
                    delivery_fee=delivery_fee,
                    delivery_limit=item.product.gd_delivery_limit,
                    real_delivery_fee=delivery_fee,
                )

            # 장바구니 정리
            Cart.objects.filter(id__in=cart_ids, member=request.user).delete()
            if 'order_cart_ids' in request.session:
                del request.session['order_cart_ids']

            # 세션에 주문 정보 저장 (결제 콜백용)
            request.session['shop_order_id'] = order.id
            request.session['shop_order_no'] = order.order_no

        good_name = first_goods_name
        if len(cart_items) > 1:
            good_name += f' 외 {len(cart_items) - 1}건'

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_no': order.order_no,
            'settle_price': settle_price,
            'good_name': good_name,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def shop_kcp_return(request):
    """KCP 결제 결과 콜백 처리"""
    if request.method != 'POST':
        return redirect('shop:goods_list')

    res_cd = request.POST.get('res_cd', '')
    res_msg = request.POST.get('res_msg', '')

    order_id = request.session.get('shop_order_id')
    if not order_id:
        return render(request, 'shop/order_fail.html', {
            'shop_menu': SHOP_MENU,
            'current_menu': 'shop_goods',
            'res_msg': '세션이 만료되었습니다. 다시 주문해주세요.',
        })

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return render(request, 'shop/order_fail.html', {
            'shop_menu': SHOP_MENU,
            'current_menu': 'shop_goods',
            'res_msg': '주문 정보를 찾을 수 없습니다.',
        })

    if res_cd == '0000':
        # 결제 성공
        order.state = 200
        order.is_finish = 'T'
        order.confirm_date = timezone.localtime()
        order.save()

        # KCP 결제 로그
        ShopPaymentKCP.objects.create(
            order=order,
            use_pay_method=request.POST.get('use_pay_method', ''),
            res_cd=res_cd,
            res_msg=res_msg,
            tno=request.POST.get('tno', ''),
            amount=int(request.POST.get('amount', 0) or 0),
            card_cd=request.POST.get('card_cd', ''),
            card_name=request.POST.get('card_name', ''),
            app_time=request.POST.get('app_time', ''),
            app_no=request.POST.get('app_no', ''),
            noinf=request.POST.get('noinf', ''),
            quota=request.POST.get('quota', ''),
            bank_name=request.POST.get('bank_name', ''),
            depositor=request.POST.get('depositor', ''),
            account=request.POST.get('account', ''),
            cash_yn=request.POST.get('cash_yn', ''),
            cash_authno=request.POST.get('cash_authno', ''),
            member_num=request.user.username,
            insert_dt=timezone.localtime(),
        )

        # 포인트 적립/사용 처리
        from apps.points.utils import calculate_shop_point, add_point_history
        save_points = calculate_shop_point(order.settle_price)
        if save_points > 0:
            add_point_history(
                member_id=request.user.username,
                member_name=request.user.name,
                app_gbn='S',
                app_point=save_points,
                point_desc='쇼핑몰구매',
                order_no=order.order_no,
            )
        if order.use_cmoney and order.use_cmoney > 0:
            add_point_history(
                member_id=request.user.username,
                member_name=request.user.name,
                app_gbn='U',
                app_point=order.use_cmoney,
                point_desc='쇼핑몰사용',
                order_no=order.order_no,
            )

        # 세션 정리
        if 'shop_order_id' in request.session:
            del request.session['shop_order_id']
        if 'shop_order_no' in request.session:
            del request.session['shop_order_no']

        return render(request, 'shop/order_success.html', {
            'shop_menu': SHOP_MENU,
            'current_menu': 'shop_goods',
            'order': order,
        })
    else:
        # 결제 실패
        return render(request, 'shop/order_fail.html', {
            'shop_menu': SHOP_MENU,
            'current_menu': 'shop_goods',
            'res_msg': res_msg or '결제에 실패하였습니다.',
        })


# ── 주문조회 ──

@login_required
def order_list(request):
    """주문/배송 조회"""
    today = timezone.localtime().date()
    default_start = today - datetime.timedelta(days=90)

    ssdate = request.GET.get('ssdate', default_start.strftime('%Y-%m-%d'))
    sedate = request.GET.get('sedate', today.strftime('%Y-%m-%d'))

    orders = Order.objects.filter(
        member=request.user,
        is_finish='T',
    ).prefetch_related('items')

    try:
        start_dt = datetime.datetime.strptime(ssdate, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(sedate, '%Y-%m-%d') + datetime.timedelta(days=1)
        orders = orders.filter(
            reg_date__gte=timezone.make_aware(start_dt),
            reg_date__lt=timezone.make_aware(end_dt),
        )
    except (ValueError, TypeError):
        pass

    orders = orders.order_by('-reg_date')

    paginator = Paginator(orders, 10)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    context = {
        'shop_menu': SHOP_MENU,
        'current_menu': 'shop_lookup',
        'page_obj': page_obj,
        'ssdate': ssdate,
        'sedate': sedate,
    }
    return render(request, 'shop/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """주문 상세"""
    order = get_object_or_404(Order, id=order_id, member=request.user)
    items = order.items.all().prefetch_related('options')
    deliveries = order.deliveries.all()

    context = {
        'shop_menu': SHOP_MENU,
        'current_menu': 'shop_lookup',
        'order': order,
        'items': items,
        'deliveries': deliveries,
    }
    return render(request, 'shop/order_detail.html', context)
