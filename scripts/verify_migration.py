"""
이관 정합성 검증 — MSSQL 원본 ↔ PostgreSQL(Django) 건수·금액 대조

실행 (로컬 PG 검증):
    python scripts/verify_migration.py

⚠️ 판정 읽는 법
  ✅ 일치        : 완벽
  🟡 적음(스킵?) : Django가 더 적음 → 이관 시 빈ID/FK없음/del_chk 로 스킵된 것일 수 있음(정상일 수도). 큰 차이면 점검.
  🔴 많음(중복?) : Django가 더 많음 → 중복 이관 의심. 반드시 점검.

컷오버 직후 이 스크립트를 돌려 🔴가 없고 차이가 예상 범위면 "정상 이관" 판단.
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
from django.apps import apps as dj
from django.db.models import Sum

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;PWD=juniordb1234'
)

# 일별 마감 데몬 확정본은 proc_dt>=FROM_DT 만 이관 → 같은 기준으로 대조
DAILY_FROM_DT = '20260101'

# (라벨, MSSQL 테이블, Django 모델, 금액컬럼(MSSQL, Django) | None [, MSSQL WHERE | None])
CHECKS = [
    ('회원',      'lf_member',           'accounts.Member',             None),
    ('자녀',      'lf_memberchild',      'accounts.MemberChild',        None),
    ('탈퇴회원',   'lf_outmember',        'accounts.OutMember',          None),
    ('구장',      'lf_stadium',          'courses.Stadium',             None),
    ('코치',      'lf_coach',            'courses.Coach',               None),
    ('강좌',      'lf_lecture',          'courses.Lecture',             None),
    ('수강신청',   'lf_fcjoin_master',    'enrollment.Enrollment',       None),
    ('수강과정',   'lf_fcjoin_course',    'enrollment.EnrollmentCourse', None),
    ('청구내역',   'lf_fcjoin_bill',      'enrollment.EnrollmentBill',   ('bill_amt', 'bill_amt')),
    ('대기자',    'lf_wait_student',     'enrollment.WaitStudent',      None),
    ('KCP결제',   'lf_pay_kcp_log',      'payments.PaymentKCP',         None),
    ('게시판',    'lf_board',            'board.Board',                 None),
    ('댓글',      'lf_boardcomment',     'board.BoardComment',          None),
    ('상담',      'lf_consult',          'consult.Consult',             None),
    ('상담답변',   'lf_con_answer',       'consult.ConsultAnswer',       None),
    ('상품',      'lf_shop_goods',       'shop.Product',                None),
    ('주문',      'lf_shop_order',       'shop.Order',                  ('SettlePrice', 'settle_price')),
    ('주문상품',   'lf_shop_order_info',  'shop.OrderItem',              None),
    ('쇼핑몰결제',  'lf_shop_pay_kcp',     'shop.ShopPaymentKCP',         None),
    ('포인트내역',  'lf_userpoint_his',    'points.PointHistory',         ('app_point', 'app_point')),
    ('SMS로그',   'em_mmt_tran_log_kyt', 'notifications.SMSLog',        None),
    # ── 일별 마감 데몬 확정본 (proc_dt>=20260101 만 이관 → MSSQL도 동일 필터로 대조) ──
    ('일별스냅샷',  'lf_daily_total_data',     'reports.DailyTotalData',     ('pay_price', 'pay_price'), f"proc_dt >= '{DAILY_FROM_DT}'"),
    ('일별코치정산', 'lf_daily_coachdata_new',  'reports.DailyCoachDataNew',  None,                        f"proc_dt >= '{DAILY_FROM_DT}'"),
]


def f(n):
    return f'{n:,}'


def main():
    try:
        conn = pyodbc.connect(MSSQL_CONN_STR, timeout=10)
    except Exception as e:
        print(f'❌ MSSQL 연결 실패: {e}')
        print('   로컬 SQLEXPRESS에 2018_junior(.bak) 복원 + ODBC Driver 17 필요')
        return 2

    cur = conn.cursor()
    print(f'대상 PG: {os.environ["DJANGO_SETTINGS_MODULE"]}')
    print(f"{'항목':<10}{'MSSQL':>12}{'Django':>12}{'차이':>10}  판정")
    print('=' * 60)

    red = yellow = 0
    for row in CHECKS:
        label, mtable, model_path, amount = row[0], row[1], row[2], row[3]
        where = row[4] if len(row) > 4 else None
        wsql = f' WHERE {where}' if where else ''
        try:
            cur.execute(f'SELECT COUNT(*) FROM {mtable}{wsql}')
            m = cur.fetchone()[0]
        except Exception as e:
            print(f'{label:<10}{"MSSQL조회실패":>12}  {str(e)[:32]}')
            continue
        model = dj.get_model(model_path)
        d = model.objects.count()
        diff = d - m
        if diff == 0:
            mark = '✅ 일치'
        elif diff < 0:
            mark = '🟡 적음(스킵?)'
            yellow += 1
        else:
            mark = '🔴 많음(중복?)'
            red += 1
        print(f'{label:<10}{f(m):>12}{f(d):>12}{diff:>+10}  {mark}')

        if amount:
            mcol, dfield = amount
            try:
                cur.execute(f'SELECT ISNULL(SUM(CAST({mcol} AS BIGINT)), 0) FROM {mtable}{wsql}')
                ms = int(cur.fetchone()[0] or 0)
                ds = int(model.objects.aggregate(s=Sum(dfield))['s'] or 0)
                sdiff = ds - ms
                smark = '✅' if sdiff == 0 else ('🟡' if sdiff < 0 else '🔴')
                print(f'  └ 금액합 {f(ms):>13}{f(ds):>12}{sdiff:>+10}  {smark}')
            except Exception as e:
                print(f'  └ 금액 조회실패: {str(e)[:40]}')

    print('=' * 60)
    if red == 0 and yellow == 0:
        print('✅ 모든 항목 건수 정확히 일치 — 이관 정상')
    else:
        print(f'결과: 🔴 {red}개 / 🟡 {yellow}개')
        if red:
            print('  🔴(Django가 더 많음=중복 의심)는 반드시 원인 점검 후 컷오버.')
        if yellow:
            print('  🟡(Django가 더 적음)은 이관 스킵 규칙(빈ID/FK없음/del_chk) 때문인지 확인.')
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
