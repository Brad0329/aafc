from django import template

register = template.Library()


@register.filter
def subtract(value, arg):
    """값에서 arg를 뺀다: {{ value|subtract:arg }}"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def page_index(counter, start_index):
    """페이지 내 순번 계산: {{ forloop.counter|page_index:page.start_index }}"""
    try:
        return int(counter) + int(start_index) - 1
    except (ValueError, TypeError):
        return counter
