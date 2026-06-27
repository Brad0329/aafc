from datetime import date

from django.core.cache import cache
from django.utils import timezone


def member_count(request):
    """프론트 헤더 '현재 회원수' (원본 ASP _include/header.asp 동일 쿼리)

    SELECT count(*) FROM LF_FCJOIN_MASTER A
      INNER JOIN LF_FCJOIN_COURSE b ON A.NO_SEQ = b.NO_SEQ
     WHERE B.BILL_CODE='1001' AND course_stats IN ('LY','LP')
       AND CONVERT(VARCHAR(6), B.COURSE_YM, 112) = '<현재 YYYYMM>'

    당월 수강확정(LY)/수강예정(LP) 인원수. 매 페이지 호출되므로 10분 캐시.
    """
    cnt = cache.get('front_member_count')
    if cnt is None:
        from apps.enrollment.models import EnrollmentCourse

        today = timezone.localdate()
        start = today.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1)
        else:
            end = date(start.year, start.month + 1, 1)

        cnt = EnrollmentCourse.objects.filter(
            bill_code='1001',
            course_stats__in=['LY', 'LP'],
            course_ym__gte=start,
            course_ym__lt=end,
        ).count()
        cache.set('front_member_count', cnt, 600)  # 10분
    return {'front_member_count': cnt}
