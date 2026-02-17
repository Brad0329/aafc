from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.board.models import Board
from apps.shop.models import Product


class StaticSitemap(Sitemap):
    """정적 페이지 사이트맵"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'main',
            'courses:greeting',
            'courses:emblem',
            'courses:waytocome',
            'courses:stadium_list',
            'courses:coach_list',
            'courses:program',
            'enrollment:apply_step1',
            'consult:consult',
            'consult:free',
            'shop:goods_list',
            'accounts:login',
            'accounts:register',
        ]

    def location(self, item):
        return reverse(item)


class BoardSitemap(Sitemap):
    """게시판 글 사이트맵"""
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return Board.objects.filter(
            del_chk='N',
            b_gbn__in=['Y', 'N', 'E', 'ST', 'PR', 'P']
        ).order_by('-b_seq')[:200]

    def location(self, obj):
        board_id = obj.b_gbn
        if board_id in ('N', 'E'):
            board_id = 'Y'
        return reverse('board:view', args=[board_id, obj.b_seq])


class ProductSitemap(Sitemap):
    """상품 사이트맵"""
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return Product.objects.filter(gd_display='Y').order_by('-gd_code')

    def location(self, obj):
        return reverse('shop:goods_view', args=[obj.gd_code])
