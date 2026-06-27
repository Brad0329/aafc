"""일별 마감 데몬 — 원본 ASP SQL 저장프로시저(sp_daily_*)를 충실 이식.

매일 밤 cron으로 실행하여 당월 데이터를 집계/스냅샷해 적재한다.
  - sp_daily_coach_data_new → reports_dailycoachdatanew (코치 정산)
  - sp_daily_total_data     → reports_dailytotaldata    (전체 수강 스냅샷)

원본과 동일하게 proc_dt(적재일)별 delete-then-insert (멱등).
청구코드 일할은 정수나눗셈(MSSQL int division)을 그대로 재현하기 위해 정수 연산을 유지한다.

사용:
  python manage.py daily_aggregate                 # 오늘/당월
  python manage.py daily_aggregate --proc-date 20260622 --month 202606
  python manage.py daily_aggregate --target coach  # coach|total|both(기본)
"""
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connection, transaction


def _default_month():
    """당월(22일 이후면 익월) — 원본 sp 기준월 계산과 동일."""
    now = datetime.now()
    y, m = now.year, now.month
    if now.day > 22:
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return f'{y}{m:02d}'


# ── 코치 정산 (sp_daily_coach_data_new 이식) ──
# 원본 그레인(enrollment×course row)·상관 서브쿼리·정수나눗셈을 그대로 옮겨 확정본과 일치시킨다.
COACH_SQL = """
INSERT INTO reports_dailycoachdatanew
(proc_dt, pay_seq, member_id, child_id, order_id, pay_dt, insert_dt, pay_method, course_ym,
 sta_code, lecture_code, coach_code, coach_name, cl_cnt,
 m1001_price, m1002_price, m1003_price, m1003_b_price, m1006_price, m1007_b_price, m1009_b_price,
 m2001_price, m2002_price, regdate)
SELECT %(proc_dt)s, no_seq, member_id, child_id, order_id, pay_dt, insert_dt, pay_method, course_ym,
       sta_code, lecture_code, coach_code,
       '(' || coach_code || ')' ||
         COALESCE((SELECT x.coach_name FROM courses_coach x WHERE x.coach_code = a.coach_code), '') AS coach_name,
       SUM(cl_cnt), SUM(m1001_price), SUM(m1002_price), SUM(m1003_price), SUM(m1003_b_price),
       SUM(m1006_price), SUM(m1007_b_price), SUM(m1009_b_price), SUM(m2001_price), SUM(m2002_price),
       now()
FROM (
    SELECT a.id AS no_seq, a.member_id, a.child_id,
           '' AS order_id, a.pay_dt, a.insert_dt, a.pay_method,
           to_char(b.course_ym, 'YYYYMM') AS course_ym,
           COALESCE((SELECT s.sta_code FROM courses_lecture l JOIN courses_stadium s ON l.stadium_id = s.id
             WHERE l.lecture_code = b.lecture_code), 0) AS sta_code,
           b.lecture_code,
           -- 원본 t_coach_code=0(코치 미지정) ↔ Django t_coach=null → 0으로 맞춤
           COALESCE((SELECT c.coach_code FROM courses_lecture l JOIN courses_coach c ON l.t_coach_id = c.id
             WHERE l.lecture_code = b.lecture_code), 0) AS coach_code,
           CASE WHEN b.bill_code = '1001' THEN 1 ELSE 0 END AS cl_cnt,
           CASE WHEN b.bill_code = '1001' THEN b.course_ym_amt ELSE 0 END AS m1001_price,
           CASE WHEN b.bill_code = '1002' THEN b.course_ym_amt ELSE 0 END AS m1002_price,
           CASE WHEN b.bill_code = '1003' THEN b.course_ym_amt ELSE 0 END AS m1003_price,
           COALESCE((SELECT SUM(x.bill_amt) FROM enrollment_enrollmentbill x
                      WHERE x.no_seq = a.id AND x.bill_code = '1003' AND x.bill_desc = '결제금액차감'), 0)
             / a.lec_period / a.lec_cycle AS m1003_b_price,
           0 AS m1006_price,
           (COALESCE((SELECT SUM(x.bill_amt) FROM enrollment_enrollmentbill x
                       WHERE x.no_seq = a.id AND x.bill_code = '1007'), 0) / a.lec_period) / a.lec_cycle AS m1007_b_price,
           CASE WHEN b.bill_code = '1001'
                THEN (COALESCE((SELECT SUM(x.bill_amt) FROM enrollment_enrollmentbill x
                                 WHERE x.no_seq = a.id AND x.bill_code = '1009'), 0) / a.lec_period) / a.lec_cycle
                ELSE 0 END AS m1009_b_price,
           CASE WHEN b.bill_code = '2001' THEN b.course_ym_amt ELSE 0 END AS m2001_price,
           CASE WHEN b.bill_code = '2002' THEN b.course_ym_amt ELSE 0 END AS m2002_price
    FROM enrollment_enrollment a
    JOIN enrollment_enrollmentcourse b ON a.id = b.no_seq
    WHERE a.pay_stats = 'PY' AND a.del_chk = 'N' AND b.course_stats = 'LY'
      AND to_char(b.course_ym, 'YYYYMM') = %(month)s
) a
GROUP BY no_seq, member_id, child_id, order_id, pay_dt, insert_dt, pay_method,
         course_ym, sta_code, lecture_code, coach_code
"""


# ── 전체 수강 스냅샷 (sp_daily_total_data 이식) ──
TOTAL_SQL = """
INSERT INTO reports_dailytotaldata
(proc_dt, rownum, no_seq, member_id, "MEMBER_NAME", child_id, mhtel, "CHILD_NAME", "CARD_NUM",
 apply_gubun, sta_name, lecture_code, lecture_title, "COACH_NAME", lec_cycle, lec_period, lecture_stats,
 pay_price, lec_price, join_price, lec_course_ym_amt, pay_stats, pay_method, "PAY_DT",
 cancel_date, cancel_code, cancel_desc, start_dt, end_dt, course_ym, course_ym_amt, insert_id, "INSERT_DT")
SELECT %(proc_dt)s,
       ROW_NUMBER() OVER (ORDER BY d.sta_name, a.child_id),
       a.id, a.member_id, COALESCE(f.name, ''), a.child_id, COALESCE(f.phone, ''),
       COALESCE(g.name, ''), COALESCE(g.card_num, ''),
       CASE a.apply_gubun WHEN 'NEW' THEN '신규입단' WHEN 'RENEW' THEN '재입단'
                          WHEN 'AGAIN' THEN '재수강' ELSE '' END,
       COALESCE(d.sta_name, ''), b.lecture_code,
       COALESCE((SELECT lecture_title FROM courses_lecture WHERE lecture_code = b.lecture_code), ''),
       COALESCE(h.coach_name, ''), COALESCE(a.lec_cycle::text, ''), COALESCE(a.lec_period::text, ''),
       CASE a.lecture_stats WHEN 'LY' THEN '수강확정' WHEN 'LP' THEN '수강예정' WHEN 'LN' THEN '퇴단'
                            WHEN 'PN' THEN '일시중지' WHEN 'LS' THEN '중도취소' ELSE '' END,
       CASE WHEN a.pay_method = 'MUCU' THEN 0 ELSE COALESCE(a.pay_price, 0) END,
       CASE WHEN a.pay_method = 'MUCU' THEN 0 ELSE COALESCE(i.lec_price, 0) END,
       CASE WHEN a.pay_method = 'MUCU' THEN 0 ELSE COALESCE(i.join_price, 0) END,
       COALESCE((SELECT SUM(course_ym_amt) FROM enrollment_enrollmentcourse x
                  WHERE x.no_seq = b.no_seq AND x.lecture_code = b.lecture_code), 0),
       CASE a.pay_stats WHEN 'PY' THEN '결제완료' WHEN 'PP' THEN '결제대기' WHEN 'PN' THEN '결제취소'
                        WHEN 'PZ' THEN '결제대기취소' WHEN 'PQ' THEN '입금확인대기' ELSE '' END,
       COALESCE(a.pay_method, ''), COALESCE(to_char(a.pay_dt, 'YYYY-MM-DD'), ''),
       COALESCE(to_char(a.cancel_date, 'YYYY-MM-DD'), ''), COALESCE(a.cancel_code, ''),
       COALESCE(a.cancel_desc, ''),
       COALESCE(a.start_dt, ''), COALESCE(a.end_dt, ''), to_char(b.course_ym, 'YYYY-MM'),
       COALESCE(b.course_ym_amt, 0),
       COALESCE(a.insert_id, ''), COALESCE(to_char(a.insert_dt, 'YYYY-MM-DD'), '')
FROM enrollment_enrollment a
JOIN enrollment_enrollmentcourse b ON a.id = b.no_seq
JOIN courses_lecture c ON b.lecture_code = c.lecture_code
JOIN courses_stadium d ON c.stadium_id = d.id
JOIN accounts_member f ON f.username = a.member_id
JOIN accounts_memberchild g ON g.child_id = a.child_id
JOIN courses_coach h ON h.id = c.coach_id
JOIN (SELECT no_seq,
             SUM(CASE WHEN LEFT(bill_code, 2) = '10' THEN bill_amt ELSE 0 END) AS lec_price,
             SUM(CASE WHEN LEFT(bill_code, 2) = '20' THEN bill_amt ELSE 0 END) AS join_price
        FROM enrollment_enrollmentbill GROUP BY no_seq) i ON i.no_seq = a.id
WHERE b.bill_code = '1001'
  AND to_char(b.course_ym, 'YYYYMM') = %(month)s
"""


class Command(BaseCommand):
    help = '일별 마감 집계/스냅샷 적재 (원본 sp_daily_* 이식)'

    def add_arguments(self, parser):
        parser.add_argument('--proc-date', default=None, help='적재일 YYYYMMDD (기본: 오늘)')
        parser.add_argument('--month', default=None, help='대상 수강년월 YYYYMM (기본: 당월/22일이후 익월)')
        parser.add_argument('--target', default='both', choices=['coach', 'total', 'both'])

    def handle(self, *args, **opts):
        proc_date = opts['proc_date'] or datetime.now().strftime('%Y%m%d')
        month = opts['month'] or _default_month()
        target = opts['target']

        with transaction.atomic():
            with connection.cursor() as cur:
                if target in ('coach', 'both'):
                    cur.execute("DELETE FROM reports_dailycoachdatanew WHERE proc_dt = %s", [proc_date])
                    cur.execute(COACH_SQL, {'proc_dt': proc_date, 'month': month})
                    self.stdout.write(self.style.SUCCESS(
                        f'[coach] proc_dt={proc_date} month={month} → {cur.rowcount} rows'))
                if target in ('total', 'both'):
                    cur.execute("DELETE FROM reports_dailytotaldata WHERE proc_dt = %s", [proc_date])
                    cur.execute(TOTAL_SQL, {'proc_dt': proc_date, 'month': month})
                    self.stdout.write(self.style.SUCCESS(
                        f'[total] proc_dt={proc_date} month={month} → {cur.rowcount} rows'))
