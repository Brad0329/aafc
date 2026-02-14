# Phase 5: 쇼핑몰 (Shopping Mall) 구현 계획

## Context
AAFC 유소년 축구 아카데미 시스템의 Classic ASP → Django 마이그레이션 Phase 5.
기존 ASP 쇼핑몰(유니폼, 축구용품, 셔틀이용료, 특강비 등)을 Django로 이관한다.
MSSQL에 22개 shop 테이블, 상품 112건, 주문 12,252건, 결제 8,218건 등 기존 데이터 이관 포함.

---

## 구현 순서 (10단계)

### Step 1: Models (12개 모델)
**파일**: `apps/shop/models.py`

| 모델 | MSSQL 원본 | 건수 | 비고 |
|------|-----------|------|------|
| Category | lf_shop_category | 16 | cate_code(unique), 계층구조(cate_parent) |
| Product | lf_shop_goods | 112 | gd_code(unique), FK→Category, 39개 필드 |
| ProductOption | lf_shop_goods_option | 93 | FK→Product(gd_code), 옵션그룹(사이즈 등) |
| ProductOptionItem | lf_shop_goods_option_item | 210 | FK→ProductOption, 옵션값(S/M/L 등) |
| ProductOptionStock | lf_shop_goods_option_stock | 210 | FK→Product, 옵션조합별 재고 |
| Cart | lf_shop_cart | 4,408 | FK→Member(username), FK→Product(gd_code) |
| CartOption | lf_shop_cart_option | 166 | FK→Cart |
| Order | lf_shop_order | 12,252 | order_no(unique), 주문자/수령인 정보, state |
| OrderItem | lf_shop_order_info | 16,407 | FK→Order, FK→Product, 상품 스냅샷 |
| OrderItemOption | lf_shop_order_option | 8,163 | FK→OrderItem |
| OrderDelivery | lf_shop_order_delivery | 16,312 | FK→Order, 송장/택배사 |
| ShopPaymentKCP | lf_shop_pay_kcp | 8,218 | 쇼핑몰 전용 KCP 결제 로그 |

**핵심 규칙**:
- 기존 패턴 따름: Korean verbose names, `del_ok`/`del_chk` soft delete, `class Meta: db_table`
- FK는 `to_field`+`db_column`으로 legacy 코드와 호환 (Board 패턴 참조)
- Order states: 100(신규)→200(입금확인)→301(배송중)→302(배송완료), 402(취소)
- 옵션 종류: ''(없음), '100'(일반), '200'(재고/가격옵션)
- 포인트 필드는 유지하되 로직은 Phase 6에서 구현

### Step 2: Django Migrations
```
python manage.py makemigrations shop
python manage.py migrate
```

### Step 3: Admin 설정
**파일**: `apps/shop/admin.py`
- CategoryAdmin: list_display, list_filter
- ProductAdmin: list_display + ProductOptionInline(TabularInline)
- OrderAdmin: list_display, fieldsets(주문기본/결제/주문자/수령인) + OrderItemInline + OrderDeliveryInline
- ShopPaymentKCPAdmin: readonly_fields (결제 로그는 수정 불가)

### Step 4: 데이터 이관 스크립트
**파일**: `scripts/migrate_shop.py`
- `migrate_board.py` 패턴 그대로: pyodbc, safe_str/checkint/make_aware, bulk_create(batch=100)
- 이관 순서 (부모→자식): Category → Product → ProductOption → ProductOptionItem → ProductOptionStock → Order → OrderItem → OrderItemOption → OrderDelivery → ShopPaymentKCP
- Cart/CartOption은 이관 생략 (오래된 장바구니 데이터는 불필요)
- Order의 PersonUid → Member FK 매핑 (username 기반, 없으면 skip)
- OrderItem의 OrderUid → Order PK 매핑 (MSSQL Uid → Django id 매핑 딕셔너리)

### Step 5: URL 설정
**파일**: `apps/shop/urls.py` (신규), `config/urls.py` (1줄 추가)

```python
# config/urls.py에 추가
path('shop/', include('apps.shop.urls')),

# apps/shop/urls.py
app_name = 'shop'
urlpatterns = [
    path('goods/', goods_list, name='goods_list'),
    path('goods/<int:gd_code>/', goods_view, name='goods_view'),
    path('cart/', cart_view, name='cart'),
    path('cart/add/', cart_add, name='cart_add'),
    path('cart/delete/', cart_delete, name='cart_delete'),
    path('order/', order_form, name='order_form'),
    path('order/create/', order_create, name='order_create'),
    path('kcp/return/', shop_kcp_return, name='kcp_return'),
    path('orders/', order_list, name='order_list'),
    path('orders/<int:order_id>/', order_detail, name='order_detail'),
    path('api/option-stock/', ajax_option_stock, name='ajax_option_stock'),
]
```

### Step 6: Views - 상품 카탈로그
**파일**: `apps/shop/views.py`

- `goods_list(request)`: 카테고리 탭 + 상품 그리드, 카테고리 필터링(GET selcate_code)
- `goods_view(request, gd_code)`: 상품 상세, 옵션 드롭다운, 수량 입력, 장바구니/바로구매 버튼
- `ajax_option_stock(request)`: 옵션 조합별 재고 확인 (GET → JSON)

### Step 7: Templates - 상품 카탈로그
**파일**: `templates/shop/goods_list.html`, `templates/shop/goods_view.html`

- ASP 디자인 그대로 복제 (sub.css의 .goods_tab, .goods_list, .good_view_sel 등 CSS 클래스 활용)
- 템플릿 구조: `{% extends "base.html" %}` → sub_contents > sub_top(shop) > sub_menu > sub_contents
- 상품 이미지 경로: `/fcdata/shop_goods/` (ASP 경로 유지 또는 media/ 매핑)

### Step 8: Views + Templates - 장바구니
- `cart_view(request)`: 장바구니 목록, 수량 표시, 총액 계산
- `cart_add(request)`: POST로 상품+옵션+수량 추가 (Cart+CartOption 생성)
- `cart_delete(request)`: POST로 장바구니 항목 삭제
- Template: `templates/shop/cart.html` (ASP cart.asp 디자인 복제)

### Step 9: Views + Templates - 주문/결제
- `order_form(request)`: 주문서 작성 (선택한 장바구니 항목 → 세션 저장, 주문자/수령인/배송/결제수단 입력)
- `order_create(request)`: @transaction.atomic으로 Order+OrderItem+OrderItemOption+OrderDelivery 생성, 장바구니 정리
- `shop_kcp_return(request)`: @csrf_exempt, KCP 결제 콜백 (기존 payments/views.py 패턴 참조), ShopPaymentKCP 생성, Order state 업데이트
- Templates: `order_form.html`, `order_success.html`, `order_fail.html`

**배송비 규칙**:
- gd_delivery_kind='101': 무료배송
- gd_delivery_kind='102': 유료배송 (gd_delivery_fee)
- gd_delivery_limit > 0 이고 주문금액 >= limit: 무료배송

### Step 10: Views + Templates - 주문조회
- `order_list(request)`: 주문 목록 + 페이지네이션 + 날짜 필터
- `order_detail(request, order_id)`: 주문 상세 (상품/옵션/배송/결제 정보)
- Templates: `order_list.html`, `order_detail.html`

---

## 수정 대상 파일 요약

| 파일 | 작업 | 설명 |
|------|------|------|
| `apps/shop/models.py` | 작성 | 12개 모델 |
| `apps/shop/admin.py` | 작성 | Admin 설정 |
| `apps/shop/views.py` | 작성 | ~12개 뷰 함수 |
| `apps/shop/urls.py` | 신규 | URL 패턴 |
| `config/urls.py` | 수정 | shop URL include 1줄 추가 |
| `templates/shop/` | 신규 | 8개 템플릿 |
| `scripts/migrate_shop.py` | 신규 | 데이터 이관 스크립트 |
| `templates/base.html` | 수정 | 쇼핑몰 메뉴 링크 연결 |

---

## 검증 방법
1. Django Admin에서 모델 확인 (Category, Product, Order 등)
2. 데이터 이관 후 건수 비교: Category(16), Product(112), Order(12,252), OrderItem(16,407)
3. 브라우저 E2E: 상품목록 → 상품상세 → 장바구니 추가 → 주문서 → 결제(테스트) → 주문조회
4. 옵션 선택 시 AJAX 재고 확인 동작 확인
5. `python manage.py runserver`로 전체 플로우 테스트
