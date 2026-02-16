"""Phase 8-7: REPORT 관리 뷰 (권한코드 'R')"""
import calendar
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
from django.db.models import Q, Sum, Count, Case, When, Value, IntegerField, CharField, F
from django.db.models.functions import Coalesce, Substr
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from .decorators import office_login_required, office_permission_required
from apps.reports.models import (
    DailyTotalData, DailyCoachData, DailyCoachDataNew,
    DailyCoachDataMonth, MonthlyData,
)
from apps.enrollment.models import (
    Enrollment, EnrollmentCourse, EnrollmentBill, Attendance,
)
from apps.courses.models import Stadium, Coach, Lecture, StadiumCoach
from apps.accounts.models import Member, MemberChild
from apps.common.models import CodeValue
from apps.shop.models import Order, OrderItem, OrderItemOption
from apps.payments.models import PaymentKCP


# ── 공통 헬퍼 ──────────────────────────────────────────

PAY_METHOD_MAP = {
    'CARD': '카드', 'ACCT': '무통장입금', 'VACCT': '가상계좌', 'CASH': '현금',
    'R': '실시간계좌이체', 'EMART': '이마트', 'LOTTE': '은평롯데몰',
    'MUCU': '다문화입금', 'MCDO': '맥도날드입금', 'SP': '방학특강',
    'SDM': '서대문구', 'SPBA': '스포츠바우처', 'GRPY': '현장결제',
    'CMS': 'CMS', 'TA': '태화복지관', 'ESNC': '동수원엔씨백화점',
    'ZEROPAY': '제로페이', 'BENEFIT': '장학혜택', 'CAU': '중대부초입금',
    'YDP': '영등포입금',
}

PAY_STATS_MAP = {
    'PY': '결제완료', 'PP': '결제대기', 'PN': '결제취소',
    'PZ': '결제대기취소', 'PQ': '입금확인대기', 'UN': '미결제',
}

LECTURE_STATS_MAP = {
    'LY': '수강확정', 'LP': '수강예정', 'LN': '퇴단',
    'PN': '일시중지', 'LS': '중도취소',
}

APPLY_GUBUN_MAP = {
    'NEW': '신규입단', 'RENEW': '재입단', 'AGAIN': '재수강', 'RE': '재등록',
}

CSR_METHODS = {'MUCU', 'MCDO', 'SP', 'SDM', 'TA', 'CAU', 'YDP'}


def _get_pay_method_display(code):
    return PAY_METHOD_MAP.get(code or '', code or '')


def _get_pay_stats_display(code):
    return PAY_STATS_MAP.get(code or '', code or '')


def _get_lecture_stats_display(code):
    return LECTURE_STATS_MAP.get(code or '', code or '')


def _get_apply_gubun_display(code):
    return APPLY_GUBUN_MAP.get(code or '', code or '')


def _default_ym():
    """기본 조회월 YYYYMM"""
    today = date.today()
    if today.day > 22:
        d = today + relativedelta(months=1)
        return d.strftime('%Y%m')
    return today.strftime('%Y%m')


def _excel_response(wb, filename):
    resp = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(resp)
    return resp


def _header_fill():
    return PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')


def _thin_border():
    side = Side(style='thin')
    return Border(top=side, bottom=side, left=side, right=side)


# ── 1. 주간회의자료 ──────────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_weekly(request):
    """주간회의자료 (weekly_report_3) - MonthlyData 기반"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        latest = MonthlyData.objects.order_by('-proc_dt').values_list('proc_dt', flat=True).first()
        search_date = (latest or _default_ym())[:6]

    # 3개월: 전전월, 전월, 기준월
    try:
        base = datetime.strptime(search_date[:6], '%Y%m')
    except (ValueError, TypeError):
        base = datetime.today().replace(day=1)
    m0 = base.strftime('%Y%m')
    m1 = (base - relativedelta(months=1)).strftime('%Y%m')
    m2 = (base - relativedelta(months=2)).strftime('%Y%m')

    exclude_sta = ['관악AI-11센터', '신도림로꼬구장']

    # 각 월별 실제 proc_dt max 값 (헤더 표시용)
    def _get_max_proc_dt(prefix):
        v = MonthlyData.objects.filter(proc_dt__startswith=prefix).order_by('-proc_dt').values_list('proc_dt', flat=True).first()
        return v or prefix

    proc_dt_m0 = _get_max_proc_dt(m0)
    proc_dt_m1 = _get_max_proc_dt(m1)
    proc_dt_m2 = _get_max_proc_dt(m2)

    def _get_month_data(exact_proc_dt):
        """해당 월의 max(proc_dt) 하루치 데이터만 조회 (ASP 원본과 동일)"""
        qs = MonthlyData.objects.filter(
            proc_dt=exact_proc_dt
        ).exclude(sta_name__in=exclude_sta)
        rows = {}
        for r in qs:
            key = (r.code_desc or '', r.sta_name or '')
            if key not in rows:
                rows[key] = {
                    'code_desc': r.code_desc, 'sta_name': r.sta_name,
                    'goal_cnt': 0, 'm_cnt': 0, 'tocl': 0,
                    'new_cl_cnt': 0, 'again_cl_cnt': 0, 'stats_lnT_cnt': 0,
                }
            d = rows[key]
            d['goal_cnt'] += r.goal_cnt or 0
            d['m_cnt'] += r.m_cnt or 0
            d['tocl'] += r.tocl or 0
            d['new_cl_cnt'] += r.newT_appl_cnt or 0
            d['again_cl_cnt'] += (r.newF_appl_cnt or 0) + (r.renewT_appl_cnt or 0) + \
                                  (r.renewF_appl_cnt or 0) + (r.again_appl_cnt or 0)
            d['stats_lnT_cnt'] += r.stats_lnT_cnt or 0
        return rows

    data2 = _get_month_data(proc_dt_m2)
    data1 = _get_month_data(proc_dt_m1)
    data0 = _get_month_data(proc_dt_m0)

    all_keys = sorted(set(list(data2.keys()) + list(data1.keys()) + list(data0.keys())))

    rows = []
    code_subtotals = {}
    grand_total = {f'{p}_{m}': 0 for p in ['goal', 'mcnt', 'tocl', 'new', 'again', 'end']
                   for m in ['m2', 'm1', 'm0']}

    prev_code = None
    for key in all_keys:
        code_desc, sta_name = key
        d2 = data2.get(key, {})
        d1 = data1.get(key, {})
        d0 = data0.get(key, {})

        row = {
            'code_desc': code_desc, 'sta_name': sta_name,
            'goal_m2': d2.get('goal_cnt', 0), 'mcnt_m2': d2.get('m_cnt', 0),
            'tocl_m2': d2.get('tocl', 0), 'new_m2': d2.get('new_cl_cnt', 0),
            'again_m2': d2.get('again_cl_cnt', 0), 'end_m2': d2.get('stats_lnT_cnt', 0),
            'goal_m1': d1.get('goal_cnt', 0), 'mcnt_m1': d1.get('m_cnt', 0),
            'tocl_m1': d1.get('tocl', 0), 'new_m1': d1.get('new_cl_cnt', 0),
            'again_m1': d1.get('again_cl_cnt', 0), 'end_m1': d1.get('stats_lnT_cnt', 0),
            'goal_m0': d0.get('goal_cnt', 0), 'mcnt_m0': d0.get('m_cnt', 0),
            'tocl_m0': d0.get('tocl', 0), 'new_m0': d0.get('new_cl_cnt', 0),
            'again_m0': d0.get('again_cl_cnt', 0), 'end_m0': d0.get('stats_lnT_cnt', 0),
            'is_subtotal': False, 'is_total': False,
        }
        row['mcnt_diff_m1'] = row['mcnt_m1'] - row['mcnt_m2']
        row['tocl_diff_m1'] = row['tocl_m1'] - row['tocl_m2']
        row['mcnt_diff_m0'] = row['mcnt_m0'] - row['mcnt_m1']
        row['tocl_diff_m0'] = row['tocl_m0'] - row['tocl_m1']

        if code_desc != prev_code and prev_code is not None and prev_code in code_subtotals:
            sub = code_subtotals[prev_code]
            sub['is_subtotal'] = True
            sub['mcnt_diff_m1'] = sub['mcnt_m1'] - sub['mcnt_m2']
            sub['tocl_diff_m1'] = sub['tocl_m1'] - sub['tocl_m2']
            sub['mcnt_diff_m0'] = sub['mcnt_m0'] - sub['mcnt_m1']
            sub['tocl_diff_m0'] = sub['tocl_m0'] - sub['tocl_m1']
            rows.append(sub)

        if code_desc not in code_subtotals:
            code_subtotals[code_desc] = {
                'code_desc': code_desc, 'sta_name': '소계',
                **{f'{p}_{m}': 0 for p in ['goal', 'mcnt', 'tocl', 'new', 'again', 'end']
                   for m in ['m2', 'm1', 'm0']},
                'is_subtotal': False, 'is_total': False,
            }
        for p in ['goal', 'mcnt', 'tocl', 'new', 'again', 'end']:
            for m in ['m2', 'm1', 'm0']:
                k = f'{p}_{m}'
                code_subtotals[code_desc][k] += row[k]
                grand_total[k] += row[k]

        rows.append(row)
        prev_code = code_desc

    if prev_code and prev_code in code_subtotals:
        sub = code_subtotals[prev_code]
        sub['is_subtotal'] = True
        sub['mcnt_diff_m1'] = sub['mcnt_m1'] - sub['mcnt_m2']
        sub['tocl_diff_m1'] = sub['tocl_m1'] - sub['tocl_m2']
        sub['mcnt_diff_m0'] = sub['mcnt_m0'] - sub['mcnt_m1']
        sub['tocl_diff_m0'] = sub['tocl_m0'] - sub['tocl_m1']
        rows.append(sub)

    grand_total['code_desc'] = 'AAFC'
    grand_total['sta_name'] = '합계'
    grand_total['is_subtotal'] = False
    grand_total['is_total'] = True
    grand_total['mcnt_diff_m1'] = grand_total['mcnt_m1'] - grand_total['mcnt_m2']
    grand_total['tocl_diff_m1'] = grand_total['tocl_m1'] - grand_total['tocl_m2']
    grand_total['mcnt_diff_m0'] = grand_total['mcnt_m0'] - grand_total['mcnt_m1']
    grand_total['tocl_diff_m0'] = grand_total['tocl_m0'] - grand_total['tocl_m1']
    rows.append(grand_total)

    return render(request, 'ba_office/lfreport/weekly_report.html', {
        'search_date': search_date, 'rows': rows,
        'month_m2': m2, 'month_m1': m1, 'month_m0': m0,
        'proc_dt_m2': proc_dt_m2, 'proc_dt_m1': proc_dt_m1, 'proc_dt_m0': proc_dt_m0,
    })


# ── 2. (Daily)전체_DATA ─────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_total_data_daily(request):
    """(Daily)전체_DATA - DailyTotalData 단순 조회"""
    sch = request.GET.get('sch_lecture_month', '')
    if not sch:
        sch = _default_ym()

    rows = DailyTotalData.objects.filter(proc_dt=sch).order_by('id')[:10000]
    data = []
    for i, r in enumerate(rows, 1):
        data.append({
            'num': i, 'no_seq': r.id, 'member_id': r.member_id,
            'member_name': r.member_name, 'child_id': r.child_id,
            'mhtel': r.mhtel, 'child_name': r.child_name,
            'card_num': r.card_num, 'apply_gubun': r.apply_gubun,
            'sta_name': r.sta_name, 'lecture_code': r.lecture_code,
            'lecture_title': r.lecture_title, 'coach_name': r.coach_name,
            'lec_cycle': r.lec_cycle, 'lec_period': r.lec_period,
            'lecture_stats': r.lecture_stats, 'pay_price': r.pay_price,
            'lec_price': r.lec_price, 'join_price': r.join_price,
            'lec_course_ym_amt': r.lec_course_ym_amt,
            'pay_stats': r.pay_stats, 'pay_method': r.pay_method,
            'pay_dt': r.pay_dt, 'cancel_date': r.cancel_date,
            'cancel_code': r.cancel_code, 'cancel_desc': r.cancel_desc,
            'start_dt': r.start_dt, 'end_dt': r.end_dt,
            'course_ym': r.course_ym, 'course_ym_amt': r.course_ym_amt,
            'insert_id': r.insert_id, 'insert_dt': r.insert_dt,
        })

    return render(request, 'ba_office/lfreport/total_data_daily.html', {
        'sch_lecture_month': sch, 'rows': data, 'total_count': len(data),
    })


@office_login_required
@office_permission_required('R')
def report_total_data_daily_excel(request):
    """(Daily)전체_DATA Excel"""
    sch = request.GET.get('sch_lecture_month', '')
    if not sch:
        return HttpResponse('조회월을 지정해주세요.')

    rows = DailyTotalData.objects.filter(proc_dt=sch).order_by('id')[:10000]

    wb = Workbook()
    ws = wb.active
    ws.title = 'Daily전체DATA'
    headers = ['순번', 'NO_SEQ', '부모아이디', '부모명', '자녀아이디', '핸드폰번호',
               '자녀명', '카드번호', '입단구분', '구장', '클래스코드', '클래스명',
               '담당코치', '수업주기', '수강기간', '수강상태', '결제금액', '수업료',
               '교육용품비', '월수강금액', '결제상태', '결제방법', '결제일자',
               '취소일자', '취소코드', '취소사유', '시작월', '종료월',
               '수강월', '수강금액', '등록자', '등록일자']
    hfill = _header_fill()
    border = _thin_border()
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = hfill
        cell.border = border
        cell.font = Font(bold=True)

    for i, r in enumerate(rows, 1):
        vals = [i, r.id, r.member_id, r.member_name, r.child_id, r.mhtel,
                r.child_name, r.card_num, r.apply_gubun, r.sta_name,
                r.lecture_code, r.lecture_title, r.coach_name,
                r.lec_cycle, r.lec_period, r.lecture_stats,
                r.pay_price, r.lec_price, r.join_price, r.lec_course_ym_amt,
                r.pay_stats, r.pay_method, r.pay_dt, r.cancel_date,
                r.cancel_code, r.cancel_desc, r.start_dt, r.end_dt,
                r.course_ym, r.course_ym_amt, r.insert_id, r.insert_dt]
        for col_idx, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=col_idx, value=v).border = border

    return _excel_response(wb, f'total_data_daily_{sch}.xlsx')


# ── 3. (회원)전체_DATA ──────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_total_data(request):
    """(회원)전체_DATA - 라이브 JOIN 쿼리"""
    sch = request.GET.get('sch_lecture_month', '')
    if not sch:
        sch = _default_ym()

    rows = _get_total_data(sch)

    return render(request, 'ba_office/lfreport/total_data.html', {
        'sch_lecture_month': sch, 'rows': rows, 'total_count': len(rows),
    })


@office_login_required
@office_permission_required('R')
def report_total_data_excel(request):
    """(회원)전체_DATA Excel"""
    sch = request.GET.get('sch_lecture_month', '')
    if not sch:
        return HttpResponse('조회월을 지정해주세요.')

    rows = _get_total_data(sch)
    wb = Workbook()
    ws = wb.active
    ws.title = '회원전체DATA'
    headers = ['순번', 'NO_SEQ', '부모아이디', '부모명', '자녀아이디', '핸드폰번호',
               '자녀명', '카드번호', '입단구분', '구장', '클래스코드', '클래스명',
               '담당코치', '수업주기', '수강기간', '수강상태', '결제금액', '수업료',
               '월수강금액', '교육용품비', '셔틀이용료', '결제상태', '결제방법', '결제일자',
               '취소일자', '취소코드', '취소사유', '시작월', '종료월',
               '수강월', '수강금액', '등록자', '등록일자', '출석', '결석', '취소',
               '쇼핑몰건수', '쇼핑몰금액']
    hfill = _header_fill()
    border = _thin_border()
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = hfill
        cell.border = border
        cell.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['no_seq'], r['member_id'], r['member_name'],
                r['child_id'], r['mhtel'], r['child_name'], r['card_num'],
                r['apply_gubun_nm'], r['sta_name'], r['lecture_code'],
                r['lecture_title'], r['coach_name'],
                f"주{r['lec_cycle']}회", f"{r['lec_period']}개월",
                r['lecture_stats_nm'], r['pay_price'], r['lec_price'],
                r['lec_course_ym_amt'], r['join_price'], r['shuttle_price'],
                r['pay_stats_nm'], r['pay_method_nm'], r['pay_dt_str'],
                r['cancel_date_str'], r['cancel_code'], r['cancel_desc'],
                r['start_dt'], r['end_dt'], r['course_ym_str'],
                r['course_ym_amt'], r['insert_id'], r['insert_dt_str'],
                r['attend_y'], r['attend_n'], r['attend_c'],
                r['shop_cnt'], r['shop_price']]
        for col_idx, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=col_idx, value=v).border = border
    return _excel_response(wb, f'total_data_{sch}.xlsx')


def _get_total_data(sch_month):
    """(회원)전체_DATA 실시간 조회 - raw SQL"""
    sql = """
    SELECT ROW_NUMBER() OVER(ORDER BY s.sta_name, e.child_id) AS rnum,
           e.id AS no_seq, e.member_id, m.name AS member_name,
           e.child_id, m.phone AS mhtel,
           mc.name AS child_name, mc.card_num,
           e.apply_gubun, s.sta_name, ec.lecture_code,
           l.lecture_title, co.coach_name,
           e.lec_cycle, e.lec_period, e.lecture_stats,
           CASE WHEN e.pay_stats = 'PY' AND e.pay_method NOT IN ('MUCU') THEN e.pay_price ELSE 0 END AS pay_price,
           COALESCE(bill_sum.lec_price, 0) AS lec_price,
           COALESCE(bill_sum.join_price, 0) AS join_price,
           COALESCE(shuttle.shuttle_price, 0) AS shuttle_price,
           ec.course_ym_amt AS lec_course_ym_amt,
           e.pay_stats, e.pay_method,
           e.pay_dt, e.cancel_date, e.cancel_code, e.cancel_desc,
           e.start_dt, e.end_dt,
           ec.course_ym, ec.course_ym_amt,
           e.insert_id, e.insert_dt,
           COALESCE(att.attend_y, 0) AS attend_y,
           COALESCE(att.attend_n, 0) AS attend_n,
           COALESCE(att.attend_c, 0) AS attend_c,
           COALESCE(shop.shop_cnt, 0) AS shop_cnt,
           COALESCE(shop.shop_price, 0) AS shop_price
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN courses_coach co ON l.coach_id = co.id
    INNER JOIN accounts_member m ON e.member_id = m.username
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    INNER JOIN (
        SELECT no_seq,
               SUM(CASE WHEN LEFT(bill_code, 2) = '10' THEN bill_amt ELSE 0 END) AS lec_price,
               SUM(CASE WHEN LEFT(bill_code, 2) = '20' THEN bill_amt ELSE 0 END) AS join_price
        FROM enrollment_enrollmentbill GROUP BY no_seq
    ) bill_sum ON e.id = bill_sum.no_seq
    LEFT JOIN (
        SELECT no_seq, SUM(course_ym_amt) AS shuttle_price
        FROM enrollment_enrollmentcourse WHERE bill_code = '1009'
        GROUP BY no_seq
    ) shuttle ON e.id = shuttle.no_seq
    LEFT JOIN (
        SELECT child_id,
               COUNT(CASE WHEN attendance_gbn IN ('Y','A') THEN 1 END) AS attend_y,
               COUNT(CASE WHEN attendance_gbn = 'N' THEN 1 END) AS attend_n,
               COUNT(CASE WHEN attendance_gbn IN ('R','D','E') THEN 1 END) AS attend_c
        FROM enrollment_attendance
        WHERE attendance_dt LIKE %s
        GROUP BY child_id
    ) att ON e.child_id = att.child_id
    LEFT JOIN (
        SELECT person_uid, COUNT(*) AS shop_cnt,
               COALESCE(SUM(total_price), 0) AS shop_price
        FROM shop_order
        WHERE is_finish = 'T' AND is_confirm = 'T'
          AND TO_CHAR(reg_date, 'YYYYMM') = %s
        GROUP BY person_uid
    ) shop ON m.username = shop.person_uid
    WHERE ec.bill_code = '1001'
      AND TO_CHAR(ec.course_ym, 'YYYYMM') = %s
    ORDER BY s.sta_name, e.child_id
    LIMIT 10000
    """
    att_prefix = sch_month[:4] + '-' + sch_month[4:6] + '%'
    with connection.cursor() as cursor:
        cursor.execute(sql, [att_prefix, sch_month, sch_month])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []
    for r in result:
        pay_dt = r['pay_dt']
        cancel_date = r['cancel_date']
        insert_dt = r['insert_dt']
        course_ym = r['course_ym']
        data.append({
            **r,
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'cancel_date_str': cancel_date.strftime('%Y-%m-%d') if cancel_date else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
            'num': r['rnum'],
        })
    return data


# ── 4. (결제월)전체_DATA ─────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_sale_list(request):
    """(결제월)전체_DATA"""
    sch = request.GET.get('sch_lecture_month', '')
    sch_pay = request.GET.get('sch_pay_stats', '')
    if not sch:
        sch = _default_ym()

    # 요약: 해당 연도의 월별 결제상태별 합계
    cur_year = sch[:4]
    summary = _get_sale_summary(cur_year)

    # 상세 리스트
    rows = _get_sale_list_data(sch, sch_pay)

    return render(request, 'ba_office/lfreport/sale_list.html', {
        'sch_lecture_month': sch, 'sch_pay_stats': sch_pay,
        'summary': summary, 'rows': rows, 'total_count': len(rows),
    })


def _get_sale_summary(cur_year):
    """결제월 요약 - 월별 결제상태별 금액"""
    qs = Enrollment.objects.filter(
        del_chk='N'
    ).extra(
        where=["COALESCE(TO_CHAR(pay_dt, 'YYYY'), TO_CHAR(insert_dt, 'YYYY')) = %s"],
        params=[cur_year]
    ).extra(
        select={'stand_dt': "COALESCE(TO_CHAR(pay_dt, 'YYYYMM'), TO_CHAR(insert_dt, 'YYYYMM'))"}
    ).values('stand_dt').annotate(
        py_price=Sum(Case(When(pay_stats='PY', then='pay_price'), default=0, output_field=IntegerField())),
        pp_price=Sum(Case(When(pay_stats='PP', then='pay_price'), default=0, output_field=IntegerField())),
        pq_price=Sum(Case(When(pay_stats='PQ', then='pay_price'), default=0, output_field=IntegerField())),
        pn_price=Sum(Case(When(pay_stats='PN', then='pay_price'), default=0, output_field=IntegerField())),
        pz_price=Sum(Case(When(pay_stats='PZ', then='pay_price'), default=0, output_field=IntegerField())),
    ).order_by('stand_dt')
    return list(qs)


def _get_sale_list_data(sch_month, sch_pay_stats=''):
    """(결제월)전체_DATA 상세"""
    sql = """
    SELECT ROW_NUMBER() OVER(ORDER BY s.sta_name, e.child_id) AS rnum,
           e.member_id, m.name AS member_name, e.child_id,
           m.phone AS mhtel, mc.name AS child_name,
           e.apply_gubun, e.lec_cycle, e.lec_period,
           e.lecture_stats, e.pay_price, e.pay_stats, e.pay_method,
           e.pay_dt, e.cancel_date, e.cancel_code, e.cancel_desc,
           e.start_dt, e.end_dt
    FROM enrollment_enrollment e
    INNER JOIN (
        SELECT no_seq, MAX(lecture_code) AS lecture_code
        FROM enrollment_enrollmentcourse
        WHERE bill_code = '1001'
          AND TO_CHAR(course_ym, 'YYYYMM') = %s
          AND course_stats IN ('LY', 'LP', 'PN')
        GROUP BY no_seq
    ) ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN accounts_member m ON e.member_id = m.username
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    WHERE 1=1
    """
    params = [sch_month]
    if sch_pay_stats:
        sql += " AND e.pay_stats = %s"
        params.append(sch_pay_stats)
    sql += " ORDER BY s.sta_name, e.child_id LIMIT 10000"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []
    for r in result:
        pay_dt = r['pay_dt']
        cancel_date = r['cancel_date']
        data.append({
            **r,
            'num': r['rnum'],
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'cancel_date_str': cancel_date.strftime('%Y-%m-%d') if cancel_date else '',
        })
    return data


@office_login_required
@office_permission_required('R')
def report_sale_list_excel(request):
    """(결제월)전체_DATA Excel"""
    sch = request.GET.get('sch_lecture_month', '')
    sch_pay = request.GET.get('sch_pay_stats', '')
    if not sch:
        return HttpResponse('조회월을 지정해주세요.')
    rows = _get_sale_list_data(sch, sch_pay)
    wb = Workbook()
    ws = wb.active
    ws.title = '결제월전체DATA'
    headers = ['순번', '부모아이디', '부모명', '자녀아이디', '핸드폰번호', '자녀명',
               '입단구분', '수업주기', '수강기간', '수강상태', '결제금액',
               '결제상태', '결제방법', '결제일자', '취소일자', '취소코드',
               '취소사유', '시작월', '종료월']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['member_id'], r['member_name'], r['child_id'],
                r['mhtel'], r['child_name'], r['apply_gubun_nm'],
                f"주{r['lec_cycle']}회", f"{r['lec_period']}개월",
                r['lecture_stats_nm'], r['pay_price'], r['pay_stats_nm'],
                r['pay_method_nm'], r['pay_dt_str'], r['cancel_date_str'],
                r['cancel_code'], r['cancel_desc'], r['start_dt'], r['end_dt']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'sale_list_{sch}.xlsx')


# ── 5. (결제일)전체_DATA ─────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_sale_day_list(request):
    """(결제일)전체_DATA"""
    stdt = request.GET.get('sch_lecture_stdt', '')
    eddt = request.GET.get('sch_lecture_eddt', '')
    if not stdt:
        today = date.today()
        stdt = today.strftime('%Y%m%d')
        eddt = stdt

    rows = _get_sale_day_data(stdt, eddt)

    # 종료월별 요약
    summary = {}
    for r in rows:
        end = r['end_dt'] or ''
        if end not in summary:
            summary[end] = 0
        summary[end] += r['pay_price'] or 0
    summary_list = sorted(summary.items())

    return render(request, 'ba_office/lfreport/sale_day_list.html', {
        'sch_lecture_stdt': stdt, 'sch_lecture_eddt': eddt,
        'rows': rows, 'total_count': len(rows), 'summary': summary_list,
    })


def _get_sale_day_data(stdt, eddt):
    """결제일 기준 데이터"""
    st = f"{stdt[:4]}-{stdt[4:6]}-{stdt[6:8]}"
    ed = f"{eddt[:4]}-{eddt[4:6]}-{eddt[6:8]}"
    sql = """
    SELECT ROW_NUMBER() OVER(ORDER BY s.sta_name, e.child_id) AS rnum,
           e.member_id, m.name AS member_name, e.child_id,
           m.phone AS mhtel, mc.name AS child_name,
           mc.birth AS child_birth,
           e.apply_gubun, e.lec_cycle, e.lec_period,
           e.lecture_stats, e.pay_price, e.pay_stats, e.pay_method,
           e.pay_dt, e.start_dt, e.end_dt, s.sta_name
    FROM enrollment_enrollment e
    INNER JOIN (
        SELECT no_seq, MAX(lecture_code) AS lecture_code
        FROM enrollment_enrollmentcourse
        WHERE bill_code = '1001' AND course_stats = 'LY'
        GROUP BY no_seq
    ) ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN accounts_member m ON e.member_id = m.username
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    WHERE e.pay_stats = 'PY'
      AND e.pay_dt::date BETWEEN %s AND %s
    ORDER BY s.sta_name, e.child_id
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [st, ed])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    today = date.today()
    data = []
    for r in result:
        birth = r.get('child_birth')
        if birth:
            try:
                age = today.year - birth.year
                if age < 0:
                    age = 0
            except Exception:
                age = 99
        else:
            age = 99
        tax_type = '비과세' if age < 13 else '과세'
        pay_dt = r['pay_dt']
        data.append({
            **r,
            'num': r['rnum'],
            'age': age, 'tax_type': tax_type,
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'birth_str': birth.strftime('%Y-%m-%d') if birth else '',
        })
    return data


@office_login_required
@office_permission_required('R')
def report_sale_day_list_excel(request):
    """(결제일)전체_DATA Excel"""
    stdt = request.GET.get('sch_lecture_stdt', '')
    eddt = request.GET.get('sch_lecture_eddt', '')
    if not stdt:
        return HttpResponse('조회일을 지정해주세요.')
    rows = _get_sale_day_data(stdt, eddt)
    wb = Workbook()
    ws = wb.active
    ws.title = '결제일전체DATA'
    headers = ['순번', '부모아이디', '부모명', '자녀아이디', '핸드폰번호', '자녀명',
               '입단구분', '수업주기', '수강기간', '수강상태', '결제금액',
               '결제상태', '결제방법', '결제일자', '시작월', '종료월',
               '생년월일', '나이', '과세여부', '구장']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['member_id'], r['member_name'], r['child_id'],
                r['mhtel'], r['child_name'], r['apply_gubun_nm'],
                f"주{r['lec_cycle']}회", f"{r['lec_period']}개월",
                r['lecture_stats_nm'], r['pay_price'], r['pay_stats_nm'],
                r['pay_method_nm'], r['pay_dt_str'], r['start_dt'], r['end_dt'],
                r['birth_str'], r['age'], r['tax_type'], r['sta_name']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'sale_day_list_{stdt}.xlsx')


# ── 6. (회원)구장별 현재원 ───────────────────────────────

@office_login_required
@office_permission_required('R')
def report_now_data(request):
    """(회원)구장별 현재원"""
    selsta = request.GET.get('selsta_code', '')
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        lecture_dt = _default_ym()

    stadiums = Stadium.objects.filter(use_gbn='Y').order_by('sta_name')
    rows = []
    if selsta:
        rows = _get_now_data(selsta, lecture_dt)

    return render(request, 'ba_office/lfreport/now_data.html', {
        'selsta_code': selsta, 'lecture_dt': lecture_dt,
        'stadiums': stadiums, 'rows': rows, 'total_count': len(rows),
    })


def _get_now_data(sta_code, lecture_dt):
    """구장별 현재원 - 3-UNION(신규수강원/재수강/CSR)"""
    csr_methods_sql = "','".join(CSR_METHODS)
    sql = f"""
    SELECT * FROM (
        SELECT ROW_NUMBER() OVER(ORDER BY child_id) AS rnum, Y.* FROM (
            SELECT e.id AS no_seq, e.child_id, mc.name AS child_name,
                   mc.school, mc.gender, mc.birth AS child_birth,
                   m.phone AS mhtel, m.email,
                   e.apply_gubun, s.sta_name, s.sta_code,
                   cv.code_desc, ec.lecture_code, l.lecture_title,
                   co.coach_name, e.lecture_stats,
                   CASE WHEN e.pay_stats='PY' AND e.pay_method NOT IN ('{csr_methods_sql}')
                        THEN e.pay_price ELSE 0 END AS pay_price,
                   COALESCE(bs.lec_price,0) AS lec_price,
                   COALESCE(bs.join_price,0) AS join_price,
                   COALESCE(bs.total_amt,0) AS total_amt,
                   e.pay_stats, e.pay_method,
                   e.pay_dt, e.lec_period, e.lec_cycle,
                   e.start_dt, e.end_dt,
                   ec.course_ym, ec.course_ym_amt,
                   e.insert_id, e.insert_dt,
                   m.address1, m.address2,
                   CASE WHEN e.apply_gubun IN ('NEW','RENEW') AND e.pay_dt IS NOT NULL
                        AND e.lecture_stats IN ('LY','LP','PN')
                        AND e.pay_method NOT IN ('{csr_methods_sql}')
                        THEN '신규수강원'
                        WHEN e.apply_gubun = 'AGAIN'
                        AND e.lecture_stats IN ('LY','LP','PN')
                        AND e.pay_method NOT IN ('{csr_methods_sql}')
                        THEN '재수강'
                        WHEN e.lecture_stats IN ('LY','LP','PN')
                        AND e.pay_method IN ('{csr_methods_sql}')
                        THEN 'CSR'
                        ELSE NULL END AS data_gbn
            FROM enrollment_enrollment e
            INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
            INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
            INNER JOIN courses_coach co ON l.coach_id = co.id
            INNER JOIN courses_stadium s ON l.stadium_id = s.id
            INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
            INNER JOIN accounts_member m ON e.member_id = m.username
            INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
            INNER JOIN (
                SELECT no_seq,
                       SUM(CASE WHEN LEFT(bill_code,2)='10' THEN bill_amt ELSE 0 END) AS lec_price,
                       SUM(CASE WHEN LEFT(bill_code,2)='20' THEN bill_amt ELSE 0 END) AS join_price,
                       SUM(bill_amt) AS total_amt
                FROM enrollment_enrollmentbill GROUP BY no_seq
            ) bs ON e.id = bs.no_seq
            WHERE ec.bill_code = '1001'
              AND TO_CHAR(ec.course_ym, 'YYYYMM') = (
                  SELECT MIN(TO_CHAR(h.course_ym, 'YYYYMM'))
                  FROM enrollment_enrollmentcourse h
                  INNER JOIN enrollment_enrollment i ON h.no_seq = i.id
                  WHERE h.bill_code = '1001'
                    AND TO_CHAR(h.course_ym, 'YYYYMM') = %s
                    AND i.child_id = e.child_id
              )
              AND s.sta_code = %s
        ) Y WHERE Y.data_gbn IS NOT NULL
    ) Z ORDER BY Z.child_id
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [lecture_dt, sta_code])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    today = date.today()
    data = []
    for r in result:
        birth = r.get('child_birth')
        if birth:
            try:
                age = today.year - birth.year + 1
            except Exception:
                age = 0
        else:
            age = 0
        gender_nm = '여자' if r.get('gender') == 'F' else '남자'
        is_mucu = r.get('pay_method') in CSR_METHODS
        pay_dt = r.get('pay_dt')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r,
            'num': r['rnum'],
            'age': age, 'gender_nm': gender_nm,
            'birth_str': birth.strftime('%Y-%m-%d') if birth else '',
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
            'display_pay_price': 0 if is_mucu else (r.get('pay_price') or 0),
            'display_lec_price': 0 if is_mucu else (r.get('lec_price') or 0),
            'display_join_price': 0 if is_mucu else (r.get('join_price') or 0),
            'display_total_amt': 0 if is_mucu else (r.get('total_amt') or 0),
        })
    return data


@office_login_required
@office_permission_required('R')
def report_now_data_excel(request):
    """(회원)구장별 현재원 Excel"""
    selsta = request.GET.get('selsta_code', '')
    lecture_dt = request.GET.get('lecture_dt', '')
    if not selsta or not lecture_dt:
        return HttpResponse('구장과 조회월을 지정해주세요.')
    rows = _get_now_data(selsta, lecture_dt)
    wb = Workbook()
    ws = wb.active
    ws.title = '구장별현재원'
    headers = ['순번', '자녀아이디', '자녀명', '학교', '성별', '생년월일', '나이',
               '전화번호', '이메일', '입단구분', '구장명', '권역', '클래스코드',
               '클래스명', '코치명', '수강상태', '결제금액', '총금액', '수업료',
               '교육용품비', '결제상태', '결제방법', '결제일자', '수강기간', '수업주기',
               '시작월', '종료월', '수강월', '수강월수강료', '등록자ID', '등록일자',
               '데이터구분', '주소1', '주소2']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['child_id'], r['child_name'], r.get('school', ''),
                r['gender_nm'], r['birth_str'], r['age'], r['mhtel'], r.get('email', ''),
                r['apply_gubun_nm'], r['sta_name'], r.get('code_desc', ''),
                r['lecture_code'], r['lecture_title'], r['coach_name'],
                r['lecture_stats_nm'], r['display_pay_price'], r['display_total_amt'],
                r['display_lec_price'], r['display_join_price'],
                r['pay_stats_nm'], r['pay_method_nm'], r['pay_dt_str'],
                f"{r['lec_period']}개월", f"주{r['lec_cycle']}회",
                r['start_dt'], r['end_dt'], r['course_ym_str'],
                r.get('course_ym_amt', 0), r['insert_id'], r['insert_dt_str'],
                r.get('data_gbn', ''), r.get('address1', ''), r.get('address2', '')]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'now_data_{lecture_dt}.xlsx')


# ── 7. 조회월 수강 통계 ─────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_now_statics_1(request):
    """조회월 수강 통계 (WITH ROLLUP 대체)"""
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        lecture_dt = _default_ym()

    sql = """
    SELECT cv.code_desc AS codegrp, cv2.code_name, s.sta_name,
           l.lecture_title, l.lecture_code,
           COALESCE(l.kapa_tot, 0) AS stu_cnt,
           COUNT(CASE WHEN e.lecture_stats = 'LY' THEN 1 END) AS sugang_yes,
           COUNT(CASE WHEN e.lecture_stats = 'LP' THEN 1 END) AS sugang_wait,
           COUNT(CASE WHEN e.lecture_stats = 'PN' THEN 1 END) AS sugang_pause,
           COUNT(CASE WHEN e.lecture_stats = 'LN' THEN 1 END) AS sugang_end
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
    LEFT JOIN common_codevalue cv2 ON s.local_code = cv2.subcode AND cv2.grpcode = 'LOCD'
    WHERE ec.bill_code = '1001'
      AND ec.course_stats IN ('LY', 'LP', 'LN', 'PN')
      AND TO_CHAR(ec.course_ym, 'YYYYMM') = %s
    GROUP BY cv.code_desc, cv2.code_name, s.sta_name,
             l.lecture_title, l.lecture_code, l.kapa_tot
    ORDER BY cv.code_desc, s.sta_name, l.lecture_code
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [lecture_dt])
        columns = [col[0] for col in cursor.description]
        raw_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Python 으로 소계/합계 계산
    rows = []
    subtotals = {}
    grand = {'stu_cnt': 0, 'sugang_yes': 0, 'sugang_wait': 0,
             'sugang_pause': 0, 'sugang_end': 0}
    prev_codegrp = None
    prev_sta = None

    for r in raw_rows:
        cg = r['codegrp'] or ''
        sn = r['sta_name'] or ''

        if prev_codegrp is not None and cg != prev_codegrp:
            if prev_codegrp in subtotals:
                rows.append({**subtotals[prev_codegrp], 'row_type': 'subtotal_code'})

        if cg not in subtotals:
            subtotals[cg] = {
                'codegrp': cg, 'code_name': '', 'sta_name': '소계',
                'lecture_title': '', 'stu_cnt': 0, 'sugang_yes': 0,
                'sugang_wait': 0, 'sugang_pause': 0, 'sugang_end': 0,
            }

        row = {**r, 'row_type': 'data'}
        rows.append(row)

        for k in ['stu_cnt', 'sugang_yes', 'sugang_wait', 'sugang_pause', 'sugang_end']:
            subtotals[cg][k] += r[k] or 0
            grand[k] += r[k] or 0

        prev_codegrp = cg

    if prev_codegrp and prev_codegrp in subtotals:
        rows.append({**subtotals[prev_codegrp], 'row_type': 'subtotal_code'})

    rows.append({
        'codegrp': '합계', 'code_name': '', 'sta_name': '',
        'lecture_title': '', 'row_type': 'total', **grand,
    })

    return render(request, 'ba_office/lfreport/now_statics_1.html', {
        'lecture_dt': lecture_dt, 'rows': rows, 'total_count': len(raw_rows),
    })


# ── 8. 신규(재)입단 리스트 ───────────────────────────────

@office_login_required
@office_permission_required('R')
def report_new_student(request):
    """신규(재)입단 리스트"""
    p_start_dt = request.GET.get('p_start_dt', '')
    if not p_start_dt:
        p_start_dt = _default_ym()

    rows = _get_new_student_data(p_start_dt)

    return render(request, 'ba_office/lfreport/new_student.html', {
        'p_start_dt': p_start_dt, 'rows': rows, 'total_count': len(rows),
    })


def _get_new_student_data(p_start_dt):
    """신규/재입단 리스트 데이터"""
    sql = """
    SELECT * FROM (
        SELECT ROW_NUMBER() OVER(ORDER BY e.pay_dt, s.sta_name, e.child_id) AS rnum,
               e.id AS no_seq, cv.code_desc, s.sta_name, l.lecture_title,
               e.child_id, mc.name AS child_name,
               e.apply_gubun, e.lecture_stats, e.pay_price, e.pay_stats, e.pay_method,
               e.pay_dt, e.cancel_date, e.cancel_desc,
               e.lec_period, e.lec_cycle, e.start_dt, e.end_dt,
               ec.course_ym, e.insert_id, e.insert_dt,
               COALESCE(bs.lec_price, 0) AS lec_price,
               COALESCE(bs.join_price, 0) AS join_price,
               CASE WHEN e.apply_gubun = 'NEW'
                    AND TO_CHAR(e.pay_dt, 'YYYYMM') = %s THEN 'Y' ELSE 'N' END AS is_new,
               CASE WHEN e.apply_gubun = 'RENEW'
                    AND TO_CHAR(e.pay_dt, 'YYYYMM') = %s THEN 'Y' ELSE 'N' END AS is_renew
        FROM enrollment_enrollment e
        INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
        INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
        INNER JOIN courses_stadium s ON l.stadium_id = s.id
        INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
        INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
        INNER JOIN (
            SELECT no_seq,
                   SUM(CASE WHEN LEFT(bill_code,2)='10' THEN bill_amt ELSE 0 END) AS lec_price,
                   SUM(CASE WHEN LEFT(bill_code,2)='20' THEN bill_amt ELSE 0 END) AS join_price
            FROM enrollment_enrollmentbill GROUP BY no_seq
        ) bs ON e.id = bs.no_seq
        WHERE ec.bill_code = '1001'
          AND TO_CHAR(ec.course_ym, 'YYYYMM') = (
              SELECT MIN(TO_CHAR(h.course_ym, 'YYYYMM'))
              FROM enrollment_enrollmentcourse h
              INNER JOIN enrollment_enrollment i ON h.no_seq = i.id
              WHERE h.bill_code = '1001'
                AND TO_CHAR(h.course_ym, 'YYYYMM') >= %s
                AND i.child_id = e.child_id
          )
    ) X
    WHERE X.is_new = 'Y' OR X.is_renew = 'Y'
    ORDER BY X.rnum
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [p_start_dt, p_start_dt, p_start_dt])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []
    for r in result:
        is_mucu = (r.get('pay_method') or '') in CSR_METHODS
        pay_dt = r.get('pay_dt')
        cancel_date = r.get('cancel_date')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r,
            'num': r['rnum'],
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'cancel_date_str': cancel_date.strftime('%Y-%m-%d') if cancel_date else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
            'display_pay_price': 0 if is_mucu else (r.get('pay_price') or 0),
            'display_lec_price': 0 if is_mucu else (r.get('lec_price') or 0),
            'display_join_price': 0 if is_mucu else (r.get('join_price') or 0),
        })
    return data


@office_login_required
@office_permission_required('R')
def report_new_student_excel(request):
    """신규(재)입단 리스트 Excel"""
    p = request.GET.get('p_start_dt', '')
    if not p:
        return HttpResponse('검색월을 지정해주세요.')
    rows = _get_new_student_data(p)
    wb = Workbook()
    ws = wb.active
    ws.title = '신규재입단'
    headers = ['순번', 'NO_SEQ', '필드', '구장', '클래스', '자녀아이디', '자녀명',
               '신규입단', '재입단', '수강상태', '결제금액', '수업료', '교육용품비',
               '결제상태', '결제방법', '결제일자', '취소일자', '취소사유',
               '수강기간', '수업주기', '시작월', '종료월', '수강월', '등록자', '등록일자']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['no_seq'], r.get('code_desc', ''), r['sta_name'],
                r['lecture_title'], r['child_id'], r['child_name'],
                r['is_new'], r['is_renew'], r['lecture_stats_nm'],
                r['display_pay_price'], r['display_lec_price'], r['display_join_price'],
                r['pay_stats_nm'], r['pay_method_nm'], r['pay_dt_str'],
                r['cancel_date_str'], r.get('cancel_desc', ''),
                f"{r['lec_period']}개월", f"주{r['lec_cycle']}회",
                r['start_dt'], r['end_dt'], r['course_ym_str'],
                r['insert_id'], r['insert_dt_str']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'new_student_{p}.xlsx')


# ── 9. 퇴단자 리스트 ────────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_end_student(request):
    """퇴단자 리스트"""
    p_start_dt = request.GET.get('p_start_dt', '')
    if not p_start_dt:
        p_start_dt = _default_ym()
    rows = _get_end_student_data(p_start_dt)
    return render(request, 'ba_office/lfreport/end_student.html', {
        'p_start_dt': p_start_dt, 'rows': rows, 'total_count': len(rows),
    })


def _get_end_student_data(p_start_dt):
    """퇴단자 데이터"""
    sql = """
    SELECT * FROM (
        SELECT ROW_NUMBER() OVER(ORDER BY e.cancel_date DESC, s.sta_name, e.child_id) AS rnum,
               e.id AS no_seq, cv.code_desc, s.sta_name, l.lecture_title, co.coach_name,
               e.child_id, mc.name AS child_name, mc.birth AS child_birth,
               m.phone AS mhtel,
               e.apply_gubun, e.lecture_stats, e.pay_price, e.pay_stats, e.pay_method,
               e.pay_dt, e.cancel_date, e.cancel_code, e.cancel_desc,
               e.lec_period, e.lec_cycle, e.start_dt, e.end_dt,
               ec.course_ym, e.insert_id, e.insert_dt,
               COALESCE(bs.lec_price, 0) AS lec_price,
               COALESCE(bs.join_price, 0) AS join_price,
               CASE WHEN e.lecture_stats = 'LN'
                    AND TO_CHAR(e.cancel_date, 'YYYYMM') = %s THEN 'Y' ELSE 'N' END AS is_end,
               CASE WHEN e.apply_gubun IN ('NEW','RENEW') AND e.pay_dt IS NULL
                    AND e.lecture_stats = 'LN'
                    AND TO_CHAR(e.cancel_date, 'YYYYMM') = %s THEN 'Y' ELSE 'N' END AS is_end_exclude
        FROM enrollment_enrollment e
        INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
        INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
        INNER JOIN courses_coach co ON l.coach_id = co.id
        INNER JOIN courses_stadium s ON l.stadium_id = s.id AND s.use_gbn = 'Y'
        INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
        INNER JOIN accounts_member m ON e.member_id = m.username
        INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
        INNER JOIN (
            SELECT no_seq,
                   SUM(CASE WHEN LEFT(bill_code,2)='10' THEN bill_amt ELSE 0 END) AS lec_price,
                   SUM(CASE WHEN LEFT(bill_code,2)='20' THEN bill_amt ELSE 0 END) AS join_price
            FROM enrollment_enrollmentbill GROUP BY no_seq
        ) bs ON e.id = bs.no_seq
        WHERE ec.bill_code = '1001'
          AND TO_CHAR(ec.course_ym, 'YYYYMM') = (
              SELECT MIN(TO_CHAR(h.course_ym, 'YYYYMM'))
              FROM enrollment_enrollmentcourse h
              INNER JOIN enrollment_enrollment i ON h.no_seq = i.id
              WHERE h.bill_code = '1001'
                AND TO_CHAR(h.course_ym, 'YYYYMM') >= %s
                AND i.child_id = e.child_id
          )
    ) X
    WHERE X.is_end = 'Y' AND X.is_end_exclude = 'N'
    ORDER BY X.rnum
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [p_start_dt, p_start_dt, p_start_dt])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # 퇴단유형 코드맵
    resn_codes = dict(
        CodeValue.objects.filter(grpcode='RESN', del_chk='N').values_list('subcode', 'code_name')
    )

    today = date.today()
    data = []
    for r in result:
        birth = r.get('child_birth')
        age = (today.year - birth.year + 1) if birth else 0
        cancel_code = str(r.get('cancel_code') or '')
        cancel_type = resn_codes.get(int(cancel_code), '') if cancel_code.isdigit() else ''
        is_mucu = (r.get('pay_method') or '') in CSR_METHODS
        pay_dt = r.get('pay_dt')
        cancel_date = r.get('cancel_date')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r,
            'num': r['rnum'], 'age': age,
            'cancel_type': cancel_type,
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'cancel_date_str': cancel_date.strftime('%Y-%m-%d') if cancel_date else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
            'display_pay_price': 0 if is_mucu else (r.get('pay_price') or 0),
            'display_lec_price': 0 if is_mucu else (r.get('lec_price') or 0),
            'display_join_price': 0 if is_mucu else (r.get('join_price') or 0),
        })
    return data


@office_login_required
@office_permission_required('R')
def report_end_student_excel(request):
    """퇴단자 리스트 Excel"""
    p = request.GET.get('p_start_dt', '')
    if not p:
        return HttpResponse('검색월을 지정해주세요.')
    rows = _get_end_student_data(p)
    wb = Workbook()
    ws = wb.active
    ws.title = '퇴단자리스트'
    headers = ['순번', 'NO_SEQ', '필드', '구장', '클래스', '코치명', '자녀아이디',
               '자녀명', '나이', '전화번호', '퇴단일자', '퇴단코드', '퇴단유형',
               '퇴단사유', '수강상태', '결제금액', '수업료', '교육용품비',
               '결제상태', '결제방법', '결제일자', '수강기간', '수업주기',
               '시작월', '종료월', '수강월', '등록자', '등록일자']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['no_seq'], r.get('code_desc', ''), r['sta_name'],
                r['lecture_title'], r['coach_name'], r['child_id'], r['child_name'],
                r['age'], r['mhtel'], r['cancel_date_str'], r.get('cancel_code', ''),
                r['cancel_type'], r.get('cancel_desc', ''),
                r['lecture_stats_nm'], r['display_pay_price'],
                r['display_lec_price'], r['display_join_price'],
                r['pay_stats_nm'], r['pay_method_nm'], r['pay_dt_str'],
                f"{r['lec_period']}개월", f"주{r['lec_cycle']}회",
                r['start_dt'], r['end_dt'], r['course_ym_str'],
                r['insert_id'], r['insert_dt_str']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'end_student_{p}.xlsx')


# ── 10. 퇴단자 통계 ─────────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_anal_end(request):
    """퇴단자 통계"""
    p_start_dt = request.GET.get('p_start_dt', '')
    if not p_start_dt:
        p_start_dt = _default_ym()

    end_rows = _get_end_student_data(p_start_dt)

    # cancel_code별 구장별 집계
    stats = {}
    cancel_codes = {
        66: '단순변심', 67: '이사', 68: '일시휴식', 69: '불만족',
        70: '가입오류', 81: '구장이동', 108: '날씨', 109: '여행연수',
        110: '부상', 111: '스케줄', 112: '장기연체', 113: 'CSR종료', 116: '기타',
    }
    for r in end_rows:
        key = (r.get('code_desc', ''), r.get('sta_name', ''))
        if key not in stats:
            stats[key] = {c: 0 for c in cancel_codes}
            stats[key]['total'] = 0
            stats[key]['code_desc'] = key[0]
            stats[key]['sta_name'] = key[1]
        cc = r.get('cancel_code')
        try:
            cc_int = int(cc) if cc else 0
        except (ValueError, TypeError):
            cc_int = 0
        stats[key]['total'] += 1
        if cc_int in cancel_codes:
            stats[key][cc_int] += 1
        else:
            stats[key][116] += 1  # 기타

    rows = sorted(stats.values(), key=lambda x: (x['code_desc'], x['sta_name']))

    # 합계
    totals = {c: 0 for c in cancel_codes}
    totals['total'] = 0
    for r in rows:
        totals['total'] += r['total']
        for c in cancel_codes:
            totals[c] += r[c]

    return render(request, 'ba_office/lfreport/anal_end.html', {
        'p_start_dt': p_start_dt, 'rows': rows, 'totals': totals,
        'cancel_codes': cancel_codes,
    })


@office_login_required
@office_permission_required('R')
def report_anal_end_excel(request):
    """퇴단자 통계 Excel"""
    p = request.GET.get('p_start_dt', '')
    if not p:
        return HttpResponse('검색월을 지정해주세요.')
    end_rows = _get_end_student_data(p)
    cancel_codes = {
        66: '단순변심', 67: '이사', 68: '일시휴식', 69: '불만족',
        70: '가입오류', 81: '구장이동', 108: '날씨', 109: '여행연수',
        110: '부상', 111: '스케줄', 112: '장기연체', 113: 'CSR종료', 116: '기타',
    }
    stats = {}
    for r in end_rows:
        key = (r.get('code_desc', ''), r.get('sta_name', ''))
        if key not in stats:
            stats[key] = {c: 0 for c in cancel_codes}
            stats[key]['total'] = 0
            stats[key]['code_desc'] = key[0]
            stats[key]['sta_name'] = key[1]
        cc = r.get('cancel_code')
        try:
            cc_int = int(cc) if cc else 0
        except (ValueError, TypeError):
            cc_int = 0
        stats[key]['total'] += 1
        if cc_int in cancel_codes:
            stats[key][cc_int] += 1
        else:
            stats[key][116] += 1
    rows = sorted(stats.values(), key=lambda x: (x['code_desc'], x['sta_name']))
    totals = {c: 0 for c in cancel_codes}
    totals['total'] = 0
    for r in rows:
        totals['total'] += r['total']
        for c in cancel_codes:
            totals[c] += r[c]
    wb = Workbook()
    ws = wb.active
    ws.title = '퇴단자통계'
    headers = ['필드', '구장', '총인원'] + list(cancel_codes.values())
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['code_desc'], r['sta_name'], r['total']] + [r[c] for c in cancel_codes]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    ri = len(rows) + 2
    ws.cell(row=ri, column=1, value='총계').font = Font(bold=True)
    ws.cell(row=ri, column=3, value=totals['total'])
    for ci, c in enumerate(cancel_codes, 4):
        ws.cell(row=ri, column=ci, value=totals[c])
    return _excel_response(wb, f'anal_end_{p}.xlsx')


# ── 11. 조회월 현재원 (검색+AJAX) ───────────────────────

@office_login_required
@office_permission_required('R')
def report_now_statics_2(request):
    """조회월 현재원 - 검색 폼"""
    lecture_dt = request.GET.get('sel_lecture_dt', '')
    if not lecture_dt:
        lecture_dt = _default_ym()

    # 권역(필드) 목록
    code_descs = list(
        CodeValue.objects.filter(grpcode='LOCD', del_chk='N')
        .values_list('code_desc', flat=True).distinct().order_by('code_desc')
    )

    return render(request, 'ba_office/lfreport/now_statics_2.html', {
        'sel_lecture_dt': lecture_dt,
        'code_descs': code_descs,
    })


@office_login_required
@office_permission_required('R')
def report_now_statics_2_load(request):
    """조회월 현재원 - AJAX 데이터 로드"""
    lecture_dt = request.GET.get('sel_lecture_dt', '')
    group_code = request.GET.get('group_code', '')
    local_code = request.GET.get('local_code', '')
    sta_code = request.GET.get('sta_code', '')
    lecture_code = request.GET.get('lecture_code', '')
    apply_gubun = request.GET.get('apply_gubun', '')
    lecture_stats = request.GET.get('lecture_stats', '')
    pay_stats = request.GET.get('pay_stats', '')

    if not lecture_dt:
        lecture_dt = _default_ym()

    sql = """
    SELECT e.id AS no_seq, e.child_id, mc.name AS child_name,
           mc.school, mc.birth AS child_birth,
           m.phone AS mhtel, m.email, m.address1, m.address2,
           e.apply_gubun, s.sta_name, cv.code_desc,
           l.lecture_title, e.lecture_stats,
           CASE WHEN e.pay_method = 'MUCU' THEN 0 ELSE e.pay_price END AS pay_price,
           COALESCE(bs.total_amt, 0) AS total_amt,
           CASE WHEN e.pay_method = 'MUCU' THEN 0 ELSE COALESCE(bs.lec_price, 0) END AS lec_price,
           CASE WHEN e.pay_method = 'MUCU' THEN 0 ELSE COALESCE(bs.join_price, 0) END AS join_price,
           e.pay_stats, e.pay_method, e.pay_dt,
           e.lec_period, e.lec_cycle, e.start_dt, e.end_dt,
           ec.course_ym, ec.course_ym_amt, e.insert_id, e.insert_dt
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
    INNER JOIN accounts_member m ON e.member_id = m.username
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    INNER JOIN (
        SELECT no_seq,
               SUM(CASE WHEN LEFT(bill_code,2)='10' THEN bill_amt ELSE 0 END) AS lec_price,
               SUM(CASE WHEN LEFT(bill_code,2)='20' THEN bill_amt ELSE 0 END) AS join_price,
               SUM(bill_amt) AS total_amt
        FROM enrollment_enrollmentbill GROUP BY no_seq
    ) bs ON e.id = bs.no_seq
    WHERE ec.bill_code = '1001'
      AND TO_CHAR(ec.course_ym, 'YYYYMM') = %s
    """
    params = [lecture_dt]

    if group_code:
        sql += " AND cv.code_desc = %s"
        params.append(group_code)
    if local_code:
        sql += " AND s.local_code = %s"
        params.append(int(local_code))
    if sta_code:
        sql += " AND s.sta_code = %s"
        params.append(int(sta_code))
    if lecture_code:
        sql += " AND ec.lecture_code = %s"
        params.append(int(lecture_code))
    if apply_gubun:
        sql += " AND e.apply_gubun = %s"
        params.append(apply_gubun)
    if lecture_stats:
        sql += " AND e.lecture_stats = %s"
        params.append(lecture_stats)
    if pay_stats:
        sql += " AND e.pay_stats = %s"
        params.append(pay_stats)

    sql += " ORDER BY s.local_code, s.sta_code, mc.name LIMIT 10000"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    today = date.today()
    data = []
    for i, r in enumerate(result, 1):
        birth = r.get('child_birth')
        age = (today.year - birth.year + 1) if birth else 0
        pay_dt = r.get('pay_dt')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r, 'num': i, 'age': age,
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
        })

    return render(request, 'ba_office/lfreport/now_statics_2_data.html', {
        'rows': data, 'total_count': len(data),
    })


def ajax_report_stadium(request):
    """REPORT > AJAX 구장 목록"""
    local_code = request.GET.get('local_code', '')
    qs = Stadium.objects.filter(use_gbn='Y')
    if local_code:
        qs = qs.filter(local_code=int(local_code))
    from django.http import JsonResponse
    return JsonResponse({
        'stadiums': list(qs.values('sta_code', 'sta_name').order_by('sta_name'))
    })


# ── 12. 쇼핑몰 주문현황 ────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_order_list(request):
    """쇼핑몰 주문현황"""
    stdt = request.GET.get('p_start_dt', '')
    eddt = request.GET.get('p_end_dt', '')
    goods_title = request.GET.get('goods_title', '')
    if not stdt:
        today = date.today()
        stdt = (today - timedelta(days=30)).strftime('%Y%m%d')
        eddt = today.strftime('%Y%m%d')

    rows = _get_order_list_data(stdt, eddt, goods_title)

    return render(request, 'ba_office/lfreport/order_list.html', {
        'p_start_dt': stdt, 'p_end_dt': eddt, 'goods_title': goods_title,
        'rows': rows, 'total_count': len(rows),
    })


def _get_order_list_data(stdt, eddt, goods_title=''):
    """쇼핑몰 주문 데이터"""
    st = f"{stdt[:4]}-{stdt[4:6]}-{stdt[6:8]}"
    ed = f"{eddt[:4]}-{eddt[4:6]}-{eddt[6:8]}"

    qs = Order.objects.filter(
        insert_dt__date__gte=st, insert_dt__date__lte=ed,
    ).select_related('member').prefetch_related('items', 'items__options').order_by('-insert_dt')

    if goods_title:
        qs = qs.filter(items__goods_title__icontains=goods_title).distinct()

    data = []
    for i, o in enumerate(qs[:5000], 1):
        for item in o.items.all():
            opts = list(item.options.all().order_by('sort'))
            opt_list = [(op.title, op.item) for op in opts]
            data.append({
                'num': i, 'uid': o.id, 'order_no': o.order_no,
                'goods_title': item.goods_title,
                'price': (item.price * item.ea) + item.option_price,
                'insert_dt': o.insert_dt.strftime('%Y-%m-%d') if o.insert_dt else '',
                'pay_dt': o.pay_dt.strftime('%Y-%m-%d') if o.pay_dt else '',
                'payway': o.payway or '',
                'state': o.get_state_display() if hasattr(o, 'get_state_display') else o.state,
                'is_cancel': '취소' if o.state == 402 else '',
                'cancel_dt': o.cancel_dt.strftime('%Y-%m-%d') if hasattr(o, 'cancel_dt') and o.cancel_dt else '',
                'ord_name': o.ord_name or '',
                'ord_phone': o.ord_phone or '',
                'ord_memo': o.ord_memo or '',
                'rcv_name': o.rcv_name or '',
                'rcv_phone': o.rcv_phone or '',
                'rcv_address': f"{o.rcv_address1 or ''} {o.rcv_address2 or ''}",
                'options': opt_list,
                'child_id': o.child_id or '',
                'ea': item.ea,
            })
    return data


@office_login_required
@office_permission_required('R')
def report_order_list_excel(request):
    """쇼핑몰 주문현황 Excel"""
    stdt = request.GET.get('p_start_dt', '')
    eddt = request.GET.get('p_end_dt', '')
    goods_title = request.GET.get('goods_title', '')
    if not stdt:
        return HttpResponse('조회일을 지정해주세요.')
    rows = _get_order_list_data(stdt, eddt, goods_title)
    wb = Workbook()
    ws = wb.active
    ws.title = '쇼핑몰주문'
    headers = ['순번', '주문번호', '상품명', '가격', '주문일자', '결제일자',
               '결제방법', '취소여부', '주문자', '주문자연락처', '주문메모',
               '수령인', '수령인연락처', '수령인주소', '자녀아이디']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['num'], r['order_no'], r['goods_title'], r['price'],
                r['insert_dt'], r['pay_dt'], r['payway'], r['is_cancel'],
                r['ord_name'], r['ord_phone'], r['ord_memo'],
                r['rcv_name'], r['rcv_phone'], r['rcv_address'], r['child_id']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'order_list_{stdt}_{eddt}.xlsx')


@office_login_required
@office_permission_required('R')
def report_order_list_dedup(request):
    """쇼핑몰 주문현황(중복제거)"""
    stdt = request.GET.get('p_start_dt', '')
    eddt = request.GET.get('p_end_dt', '')
    goods_title = request.GET.get('goods_title', '')
    if not stdt:
        today = date.today()
        stdt = (today - timedelta(days=30)).strftime('%Y%m%d')
        eddt = today.strftime('%Y%m%d')

    rows = _get_order_list_data(stdt, eddt, goods_title)
    # 중복제거: child_id당 1건만
    seen = set()
    dedup = []
    for r in rows:
        cid = r.get('child_id', '')
        if cid and cid in seen:
            continue
        if cid:
            seen.add(cid)
        dedup.append(r)

    return render(request, 'ba_office/lfreport/order_list.html', {
        'p_start_dt': stdt, 'p_end_dt': eddt, 'goods_title': goods_title,
        'rows': dedup, 'total_count': len(dedup), 'is_dedup': True,
    })


@office_login_required
@office_permission_required('R')
def report_order_list_dedup_excel(request):
    """쇼핑몰 주문현황(중복제거) Excel"""
    stdt = request.GET.get('p_start_dt', '')
    eddt = request.GET.get('p_end_dt', '')
    goods_title = request.GET.get('goods_title', '')
    if not stdt:
        return HttpResponse('조회일을 지정해주세요.')
    rows = _get_order_list_data(stdt, eddt, goods_title)
    seen = set()
    dedup = []
    for r in rows:
        cid = r.get('child_id', '')
        if cid and cid in seen:
            continue
        if cid:
            seen.add(cid)
        dedup.append(r)
    wb = Workbook()
    ws = wb.active
    ws.title = '쇼핑몰주문(중복제거)'
    headers = ['순번', '주문번호', '상품명', '가격', '주문일자', '결제일자',
               '결제방법', '취소여부', '주문자', '주문자연락처', '자녀아이디']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(dedup, 1):
        vals = [i, r['order_no'], r['goods_title'], r['price'],
                r['insert_dt'], r['pay_dt'], r['payway'], r['is_cancel'],
                r['ord_name'], r['ord_phone'], r['child_id']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'order_list_dedup_{stdt}_{eddt}.xlsx')


# ── 13. 미납자관리 ──────────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_delay_data(request):
    """미납자관리"""
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        lecture_dt = _default_ym()

    sql = """
    SELECT e.id AS no_seq, e.child_id, mc.name AS child_name,
           m.phone AS mhtel, m.name AS member_name,
           s.sta_name, cv.code_desc, l.lecture_title, co.coach_name,
           e.apply_gubun, e.lecture_stats, e.pay_price, e.pay_stats, e.pay_method,
           e.pay_dt, e.lec_period, e.lec_cycle, e.start_dt, e.end_dt,
           ec.course_ym, ec.course_ym_amt, e.insert_id, e.insert_dt,
           e.bigo_content
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_coach co ON l.coach_id = co.id
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
    INNER JOIN accounts_member m ON e.member_id = m.username
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    WHERE ec.bill_code = '1001'
      AND TO_CHAR(ec.course_ym, 'YYYYMM') = %s
      AND e.lecture_stats IN ('LY', 'LP', 'PN')
      AND e.pay_stats NOT IN ('PY')
    ORDER BY s.sta_name, e.child_id
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [lecture_dt])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []
    for i, r in enumerate(result, 1):
        pay_dt = r.get('pay_dt')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r, 'num': i,
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
        })

    return render(request, 'ba_office/lfreport/delay_data.html', {
        'lecture_dt': lecture_dt, 'rows': data, 'total_count': len(data),
    })


@office_login_required
@office_permission_required('R')
def report_delay_data_excel(request):
    """미납자관리 Excel"""
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        return HttpResponse('조회월을 지정해주세요.')
    # 동일 쿼리 재사용
    request_copy = type('Request', (), {'GET': {'lecture_dt': lecture_dt}})()
    # 직접 쿼리
    sql = """
    SELECT e.id AS no_seq, e.child_id, mc.name AS child_name,
           m.phone AS mhtel, m.name AS member_name,
           s.sta_name, cv.code_desc, l.lecture_title, co.coach_name,
           e.apply_gubun, e.lecture_stats, e.pay_price, e.pay_stats, e.pay_method,
           e.pay_dt, e.lec_period, e.lec_cycle, e.start_dt, e.end_dt,
           ec.course_ym, ec.course_ym_amt, e.insert_id, e.insert_dt
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_coach co ON l.coach_id = co.id
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
    INNER JOIN accounts_member m ON e.member_id = m.username
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    WHERE ec.bill_code = '1001'
      AND TO_CHAR(ec.course_ym, 'YYYYMM') = %s
      AND e.lecture_stats IN ('LY', 'LP', 'PN')
      AND e.pay_stats NOT IN ('PY')
    ORDER BY s.sta_name, e.child_id
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [lecture_dt])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    wb = Workbook()
    ws = wb.active
    ws.title = '미납자관리'
    headers = ['순번', '구장', '코치', '자녀아이디', '자녀명', '전화번호',
               '입단구분', '수강상태', '결제금액', '결제상태', '결제방법',
               '수강기간', '수업주기', '시작월', '종료월', '수강월']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(result, 1):
        course_ym = r.get('course_ym')
        vals = [i, r['sta_name'], r['coach_name'], r['child_id'], r['child_name'],
                r['mhtel'], _get_apply_gubun_display(r['apply_gubun']),
                _get_lecture_stats_display(r['lecture_stats']), r['pay_price'],
                _get_pay_stats_display(r['pay_stats']),
                _get_pay_method_display(r['pay_method']),
                f"{r['lec_period']}개월", f"주{r['lec_cycle']}회",
                r['start_dt'], r['end_dt'],
                course_ym.strftime('%Y-%m') if course_ym else '']
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'delay_data_{lecture_dt}.xlsx')


# ── 14. 월별출결현황 ────────────────────────────────────

@office_login_required
@office_permission_required('R')
def report_attendance_month(request):
    """월별출결현황"""
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        lecture_dt = date.today().strftime('%Y%m')

    ym_prefix = f"{lecture_dt[:4]}-{lecture_dt[4:6]}"

    sql = """
    SELECT s.sta_name, l.lecture_title, co.coach_name,
           COUNT(CASE WHEN a.attendance_gbn = 'Y' THEN 1 END) AS att_y,
           COUNT(CASE WHEN a.attendance_gbn = 'A' THEN 1 END) AS att_a,
           COUNT(CASE WHEN a.attendance_gbn = 'N' THEN 1 END) AS att_n,
           COUNT(CASE WHEN a.attendance_gbn = 'R' THEN 1 END) AS att_r,
           COUNT(CASE WHEN a.attendance_gbn = 'D' THEN 1 END) AS att_d,
           COUNT(CASE WHEN a.attendance_gbn = 'E' THEN 1 END) AS att_e,
           COUNT(*) AS att_total
    FROM enrollment_attendance a
    INNER JOIN courses_lecture l ON a.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON a.sta_code = s.sta_code
    INNER JOIN courses_coach co ON l.coach_id = co.id
    WHERE a.attendance_dt LIKE %s
    GROUP BY s.sta_name, l.lecture_title, co.coach_name
    ORDER BY s.sta_name, l.lecture_title
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [ym_prefix + '%'])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'ba_office/lfreport/attendance_month.html', {
        'lecture_dt': lecture_dt, 'rows': result, 'total_count': len(result),
    })


@office_login_required
@office_permission_required('R')
def report_attendance_month_excel(request):
    """월별출결현황 Excel"""
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        return HttpResponse('조회월을 지정해주세요.')
    ym_prefix = f"{lecture_dt[:4]}-{lecture_dt[4:6]}"
    sql = """
    SELECT s.sta_name, l.lecture_title, co.coach_name,
           COUNT(CASE WHEN a.attendance_gbn = 'Y' THEN 1 END) AS att_y,
           COUNT(CASE WHEN a.attendance_gbn = 'A' THEN 1 END) AS att_a,
           COUNT(CASE WHEN a.attendance_gbn = 'N' THEN 1 END) AS att_n,
           COUNT(CASE WHEN a.attendance_gbn = 'R' THEN 1 END) AS att_r,
           COUNT(CASE WHEN a.attendance_gbn = 'D' THEN 1 END) AS att_d,
           COUNT(CASE WHEN a.attendance_gbn = 'E' THEN 1 END) AS att_e,
           COUNT(*) AS att_total
    FROM enrollment_attendance a
    INNER JOIN courses_lecture l ON a.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON a.sta_code = s.sta_code
    INNER JOIN courses_coach co ON l.coach_id = co.id
    WHERE a.attendance_dt LIKE %s
    GROUP BY s.sta_name, l.lecture_title, co.coach_name
    ORDER BY s.sta_name, l.lecture_title
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [ym_prefix + '%'])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]
    wb = Workbook()
    ws = wb.active
    ws.title = '월별출결'
    headers = ['구장', '클래스', '코치', '출석(Y)', '보강(A)', '결석(N)',
               '우천(R)', '연기(D)', '제외(E)', '합계']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(result, 1):
        vals = [r['sta_name'], r['lecture_title'], r['coach_name'],
                r['att_y'], r['att_a'], r['att_n'],
                r['att_r'], r['att_d'], r['att_e'], r['att_total']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'attendance_month_{lecture_dt}.xlsx')


# ── 15. 연도별 구장별 현황 ──────────────────────────────

@office_login_required
@office_permission_required('R')
def report_stadium_year(request):
    """연도별 구장별 현황"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        search_date = str(date.today().year)

    rows = MonthlyData.objects.filter(
        proc_dt__startswith=search_date
    ).values('sta_name', 'sta_code').annotate(
        total_m_cnt=Sum('m_cnt'),
        total_goal=Sum('goal_cnt'),
        total_tocl=Sum('tocl'),
        total_new=Sum('newT_appl_cnt'),
        total_renew=Sum('renewT_appl_cnt'),
        total_again=Sum('again_appl_cnt'),
        total_end=Sum('stats_lnT_cnt'),
    ).order_by('sta_name')

    return render(request, 'ba_office/lfreport/stadium_year.html', {
        'search_date': search_date, 'rows': rows, 'total_count': len(rows),
    })


@office_login_required
@office_permission_required('R')
def report_stadium_year_excel(request):
    """연도별 구장별 현황 Excel"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        return HttpResponse('조회년도를 지정해주세요.')
    rows = MonthlyData.objects.filter(
        proc_dt__startswith=search_date
    ).values('sta_name').annotate(
        total_m_cnt=Sum('m_cnt'), total_goal=Sum('goal_cnt'),
        total_tocl=Sum('tocl'), total_new=Sum('newT_appl_cnt'),
        total_renew=Sum('renewT_appl_cnt'), total_again=Sum('again_appl_cnt'),
        total_end=Sum('stats_lnT_cnt'),
    ).order_by('sta_name')
    wb = Workbook()
    ws = wb.active
    ws.title = '구장별현황'
    headers = ['구장', '회원수', '목표', '클래스', '신규', '갱신', '재입단', '퇴단']
    hfill = _header_fill()
    border = _thin_border()
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.fill = hfill
        c.border = border
        c.font = Font(bold=True)
    for i, r in enumerate(rows, 1):
        vals = [r['sta_name'], r['total_m_cnt'], r['total_goal'],
                r['total_tocl'], r['total_new'], r['total_renew'],
                r['total_again'], r['total_end']]
        for ci, v in enumerate(vals, 1):
            ws.cell(row=i + 1, column=ci, value=v).border = border
    return _excel_response(wb, f'stadium_year_{search_date}.xlsx')


# ── 16. 코치 실적 미반영 취소 ───────────────────────────

@office_login_required
@office_permission_required('R')
def report_coach_miban(request):
    """코치 실적 미반영 취소 - 결제없이 퇴단한 건"""
    lecture_dt = request.GET.get('lecture_dt', '')
    if not lecture_dt:
        lecture_dt = _default_ym()

    sql = """
    SELECT e.id AS no_seq, cv.code_desc, s.sta_name, l.lecture_title,
           e.child_id, mc.name AS child_name,
           e.lecture_stats, e.cancel_date, e.cancel_code, e.cancel_desc,
           e.pay_price, e.pay_stats, e.pay_method,
           COALESCE(bs.lec_price, 0) AS lec_price,
           COALESCE(bs.join_price, 0) AS join_price,
           e.pay_dt, e.lec_period, e.lec_cycle, e.start_dt, e.end_dt,
           ec.course_ym, e.insert_id, e.insert_dt
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN common_codevalue cv ON s.local_code = cv.subcode AND cv.grpcode = 'LOCD'
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    INNER JOIN (
        SELECT no_seq,
               SUM(CASE WHEN LEFT(bill_code,2)='10' THEN bill_amt ELSE 0 END) AS lec_price,
               SUM(CASE WHEN LEFT(bill_code,2)='20' THEN bill_amt ELSE 0 END) AS join_price
        FROM enrollment_enrollmentbill GROUP BY no_seq
    ) bs ON e.id = bs.no_seq
    WHERE ec.bill_code = '1001'
      AND TO_CHAR(ec.course_ym, 'YYYYMM') = %s
      AND e.lecture_stats = 'LN'
      AND e.apply_gubun IN ('NEW', 'RENEW')
      AND e.pay_dt IS NULL
      AND TO_CHAR(e.cancel_date, 'YYYYMM') = %s
    ORDER BY s.sta_name, e.child_id
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [lecture_dt, lecture_dt])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []
    for i, r in enumerate(result, 1):
        cancel_date = r.get('cancel_date')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r, 'num': i,
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'cancel_date_str': cancel_date.strftime('%Y-%m-%d') if cancel_date else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
        })

    return render(request, 'ba_office/lfreport/coach_miban.html', {
        'lecture_dt': lecture_dt, 'rows': data, 'total_count': len(data),
    })


# ── 17~21. Performance (코치별 현황) ────────────────────

@office_login_required
@office_permission_required('R')
def report_each_coachdata(request):
    """코치별현황 NEW (년간 코치 개별) - DailyCoachDataMonth"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        search_date = str(date.today().year)

    qs = DailyCoachDataMonth.objects.filter(
        course_ym__startswith=search_date
    ).values('sta_code', 'coach_code', 'coach_name', 'course_ym').annotate(
        total_cnt=Sum('cl_cnt'),
        total_m1001=Sum('m1001_price'), total_m1002=Sum('m1002_price'),
        total_m1003=Sum('m1003_price'), total_m1003b=Sum('m1003_b_price'),
        total_m1006=Sum('m1006_price'), total_m1007b=Sum('m1007_b_price'),
        total_m1009b=Sum('m1009_b_price'),
        total_m2001=Sum('m2001_price'), total_m2002=Sum('m2002_price'),
    ).order_by('coach_name', 'course_ym')

    # 구장명 매핑
    sta_map = dict(Stadium.objects.values_list('sta_code', 'sta_name'))

    data = []
    for r in qs:
        tot = (r['total_m1001'] or 0) + (r['total_m1002'] or 0) + \
              (r['total_m1003'] or 0) + (r['total_m1003b'] or 0) + \
              (r['total_m1006'] or 0) + (r['total_m1007b'] or 0)
        etc = (r['total_m1009b'] or 0) + (r['total_m2001'] or 0) + (r['total_m2002'] or 0)
        data.append({
            **r,
            'sta_name': sta_map.get(r['sta_code'], ''),
            'tot_sum': tot, 'etc_sum': etc,
        })

    return render(request, 'ba_office/lfreport/each_coachdata.html', {
        'search_date': search_date, 'rows': data, 'total_count': len(data),
    })


@office_login_required
@office_permission_required('R')
def report_pay_master(request):
    """월별 결제 DATA - DailyCoachDataNew"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        search_date = _default_ym()

    qs = DailyCoachDataNew.objects.filter(
        course_ym=search_date
    ).order_by('coach_name', 'sta_code')

    sta_map = dict(Stadium.objects.values_list('sta_code', 'sta_name'))

    data = []
    for i, r in enumerate(qs[:10000], 1):
        kcp_yn = 'YES' if r.order_id else 'NO'
        tot = r.m1001_price + r.m1002_price + r.m1003_price + \
              r.m1003_b_price + r.m1006_price + r.m1007_b_price
        etc = r.m1009_b_price + r.m2001_price + r.m2002_price
        data.append({
            'num': i, 'sta_name': sta_map.get(r.sta_code, ''),
            'coach_name': r.coach_name, 'kcp_yn': kcp_yn,
            'pay_method': _get_pay_method_display(r.pay_method),
            'cl_cnt': r.cl_cnt,
            'm1001': r.m1001_price, 'm1002': r.m1002_price,
            'm1003': r.m1003_price, 'm1003b': r.m1003_b_price,
            'm1006': r.m1006_price, 'm1007b': r.m1007_b_price,
            'm1009b': r.m1009_b_price,
            'm2001': r.m2001_price, 'm2002': r.m2002_price,
            'tot_sum': tot, 'etc_sum': etc,
        })

    return render(request, 'ba_office/lfreport/pay_master.html', {
        'search_date': search_date, 'rows': data, 'total_count': len(data),
    })


@office_login_required
@office_permission_required('R')
def report_raw_data(request):
    """수강 RAW DATA"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        search_date = _default_ym()

    sql = """
    SELECT e.id AS no_seq, e.member_id, e.child_id,
           mc.name AS child_name, s.sta_name, l.lecture_title,
           co.coach_name, e.apply_gubun, e.lecture_stats,
           e.pay_price, e.pay_stats, e.pay_method,
           e.pay_dt, e.lec_period, e.lec_cycle,
           e.start_dt, e.end_dt, ec.course_ym, ec.course_ym_amt,
           ec.bill_code, e.insert_dt
    FROM enrollment_enrollment e
    INNER JOIN enrollment_enrollmentcourse ec ON e.id = ec.no_seq
    INNER JOIN courses_lecture l ON ec.lecture_code = l.lecture_code
    INNER JOIN courses_stadium s ON l.stadium_id = s.id
    INNER JOIN courses_coach co ON l.coach_id = co.id
    INNER JOIN accounts_memberchild mc ON e.child_id = mc.child_id
    WHERE TO_CHAR(ec.course_ym, 'YYYYMM') = %s
    ORDER BY s.sta_name, co.coach_name, e.child_id
    LIMIT 10000
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [search_date])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []
    for i, r in enumerate(result, 1):
        pay_dt = r.get('pay_dt')
        insert_dt = r.get('insert_dt')
        course_ym = r.get('course_ym')
        data.append({
            **r, 'num': i,
            'apply_gubun_nm': _get_apply_gubun_display(r['apply_gubun']),
            'lecture_stats_nm': _get_lecture_stats_display(r['lecture_stats']),
            'pay_stats_nm': _get_pay_stats_display(r['pay_stats']),
            'pay_method_nm': _get_pay_method_display(r['pay_method']),
            'pay_dt_str': pay_dt.strftime('%Y-%m-%d') if pay_dt else '',
            'insert_dt_str': insert_dt.strftime('%Y-%m-%d') if insert_dt else '',
            'course_ym_str': course_ym.strftime('%Y-%m') if course_ym else '',
        })

    return render(request, 'ba_office/lfreport/raw_data.html', {
        'search_date': search_date, 'rows': data, 'total_count': len(data),
    })


@office_login_required
@office_permission_required('R')
def report_month_coachdata(request):
    """월별 코치 전체 - DailyCoachDataMonth ROLLUP"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        search_date = _default_ym()

    qs = DailyCoachDataMonth.objects.filter(course_ym=search_date)

    sta_map = dict(Stadium.objects.values_list('sta_code', 'sta_name'))

    raw = []
    for r in qs:
        kcp_yn = 'YES' if r.order_id else 'NO'
        tot = r.m1001_price + r.m1002_price + r.m1003_price + \
              r.m1003_b_price + r.m1006_price + r.m1007_b_price
        etc = r.m1009_b_price + r.m2001_price + r.m2002_price
        raw.append({
            'sta_name': sta_map.get(r.sta_code, ''),
            'coach_name': r.coach_name, 'kcp_yn': kcp_yn,
            'pay_method': _get_pay_method_display(r.pay_method),
            'cl_cnt': r.cl_cnt,
            'm1001': r.m1001_price, 'm1002': r.m1002_price,
            'm1003': r.m1003_price, 'm1003b': r.m1003_b_price,
            'm1006': r.m1006_price, 'm1007b': r.m1007_b_price,
            'm1009b': r.m1009_b_price,
            'm2001': r.m2001_price, 'm2002': r.m2002_price,
            'tot_sum': tot, 'etc_sum': etc,
        })

    return render(request, 'ba_office/lfreport/month_coachdata.html', {
        'search_date': search_date, 'rows': raw, 'total_count': len(raw),
    })


@office_login_required
@office_permission_required('R')
def report_year_coachdata(request):
    """년간 코치 전체 - DailyCoachDataMonth 연간 피벗"""
    search_date = request.GET.get('search_date', '')
    if not search_date:
        search_date = str(date.today().year)

    sta_map = dict(Stadium.objects.values_list('sta_code', 'sta_name'))

    qs = DailyCoachDataMonth.objects.filter(
        course_ym__startswith=search_date
    ).values(
        'sta_code', 'coach_name'
    )
    # 12개월 피벗
    for m in range(1, 13):
        mm = f"{m:02d}"
        ym = f"{search_date}{mm}"
        qs = qs.annotate(**{
            f'cnt_{mm}': Sum(Case(
                When(course_ym=ym, then='cl_cnt'), default=0, output_field=IntegerField()
            )),
            f'tot_{mm}': Sum(Case(
                When(course_ym=ym, then=F('m1001_price') + F('m1002_price') +
                     F('m1003_price') + F('m1003_b_price') +
                     F('m1006_price') + F('m1007_b_price')),
                default=0, output_field=IntegerField()
            )),
        })

    qs = qs.order_by('sta_code', 'coach_name')

    data = []
    for r in qs:
        r['sta_name'] = sta_map.get(r['sta_code'], '')
        data.append(r)

    return render(request, 'ba_office/lfreport/year_coachdata.html', {
        'search_date': search_date, 'rows': data, 'total_count': len(data),
    })
