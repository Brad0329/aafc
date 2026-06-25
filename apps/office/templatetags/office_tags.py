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


@register.filter
def dict_get(d, key):
    """딕셔너리에서 키로 값 조회: {{ mydict|dict_get:key }}"""
    if isinstance(d, dict):
        return d.get(key, '')
    return ''


# 원본 ASP function.Util.asp 의 getApplyGubun / getLectureStats 와 동일 매핑
_APPLY_GUBUN = {'NEW': '신규입단', 'AGAIN': '재수강', 'RENEW': '재입단'}
_LECTURE_STATS = {
    'LY': '수강확정', 'LP': '수강예정', 'LN': '퇴단', 'PN': '일시중지', 'LS': '중도취소',
    'C': '수강확정', 'E': '수강예정', 'F': '수강취소',
}


@register.filter
def apply_gubun_label(code):
    """신청구분 코드 → 라벨 (ASP getApplyGubun 동일): {{ code|apply_gubun_label }}"""
    return _APPLY_GUBUN.get((code or '').strip(), '-')


@register.filter
def lecture_stats_label(code):
    """수강상태 코드 → 라벨 (ASP getLectureStats 동일): {{ code|lecture_stats_label }}"""
    return _LECTURE_STATS.get((code or '').strip(), '-')
