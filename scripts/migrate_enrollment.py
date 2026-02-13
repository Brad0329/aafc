"""
MSSQL → PostgreSQL 수강신청/결제 데이터 이관 스크립트
실행: python scripts/migrate_enrollment.py
"""
import os
import sys
from pathlib import Path
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

import pyodbc
from django.utils import timezone
from apps.courses.models import LectureSelDay, PromotionMember
from apps.enrollment.models import Enrollment, EnrollmentCourse, EnrollmentBill, WaitStudent
from apps.payments.models import PaymentKCP, PaymentFail
from apps.accounts.models import Member, MemberChild

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def make_aware(dt):
    """naive datetime → aware datetime (Asia/Seoul)"""
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def checkint(val):
    """안전한 정수 변환"""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def safe_str(val):
    """안전한 문자열 변환 (MSSQL에서 int로 오는 경우 대비)"""
    if val is None:
        return ''
    return str(val).strip()


def safe_date(val):
    """datetime → date 변환"""
    if val is None:
        return None
    if hasattr(val, 'date'):
        return val.date()
    if isinstance(val, date):
        return val
    return None


def migrate_lecture_seldays(cursor):
    """lf_lecture_selday → LectureSelDay"""
    cursor.execute("""
        SELECT lecture_code, syear, smonth, sday, admin_id
          FROM lf_lecture_selday
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        lec_code = checkint(data['lecture_code'])
        syear = checkint(data['syear'])
        smonth = checkint(data['smonth'])
        sday = checkint(data['sday'])

        if not all([lec_code, syear, smonth, sday]):
            continue

        LectureSelDay.objects.update_or_create(
            lecture_code=lec_code,
            syear=syear,
            smonth=smonth,
            sday=sday,
            defaults={
                'admin_id': safe_str(data.get('admin_id', '')),
            }
        )
        count += 1

    print(f'LectureSelDay: {count}건 이관 완료')


def migrate_promotion_members(cursor):
    """lf_promotion_member → PromotionMember"""
    try:
        cursor.execute("""
            SELECT coupon_uid, member_id, child_id, used, is_trash
              FROM lf_promotion_member
        """)
    except pyodbc.ProgrammingError:
        print('PromotionMember: lf_promotion_member 테이블 없음 - 스킵')
        return

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        PromotionMember.objects.update_or_create(
            coupon_uid=checkint(data['coupon_uid']),
            member_id=safe_str(data['member_id']),
            child_id=safe_str(data['child_id']),
            defaults={
                'used': safe_str(data.get('used', 'T')) or 'T',
                'is_trash': safe_str(data.get('is_trash', 'T')) or 'T',
            }
        )
        count += 1

    print(f'PromotionMember: {count}건 이관 완료')


def migrate_enrollments(cursor):
    """lf_fcjoin_master → Enrollment (PK 보존)"""
    cursor.execute("""
        SELECT no_seq, member_id, child_id, pay_stats, pay_method,
               pay_price, pay_dt, lecture_stats, lec_cycle, lec_period,
               start_dt, end_dt, apply_gubun, source_gubun,
               recommend_id, discount_id, discount_price,
               del_chk, insert_id, insert_dt
          FROM lf_fcjoin_master
         ORDER BY no_seq
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    # 유효 member_id, child_id 세트 캐시
    valid_members = set(Member.objects.values_list('username', flat=True))
    valid_children = set(MemberChild.objects.values_list('child_id', flat=True))

    for row in rows:
        data = dict(zip(columns, row))
        member_id = safe_str(data['member_id'])
        child_id = safe_str(data['child_id'])

        if member_id not in valid_members or child_id not in valid_children:
            skipped += 1
            continue

        no_seq = checkint(data['no_seq'])
        insert_dt = make_aware(data['insert_dt'])

        Enrollment.objects.update_or_create(
            id=no_seq,
            defaults={
                'member_id': member_id,
                'child_id': child_id,
                'pay_stats': safe_str(data['pay_stats']) or 'UN',
                'pay_method': safe_str(data['pay_method']),
                'pay_price': checkint(data['pay_price']),
                'pay_dt': make_aware(data['pay_dt']),
                'lecture_stats': safe_str(data['lecture_stats']) or 'LN',
                'lec_cycle': checkint(data['lec_cycle']) or 1,
                'lec_period': checkint(data['lec_period']) or 3,
                'start_dt': safe_str(data['start_dt']),
                'end_dt': safe_str(data['end_dt']),
                'apply_gubun': safe_str(data['apply_gubun']) or 'NEW',
                'source_gubun': safe_str(data['source_gubun']) or '01',
                'recommend_id': safe_str(data['recommend_id']),
                'discount1_id': safe_str(data['discount_id']),
                'discount1_price': checkint(data['discount_price']),
                'del_chk': safe_str(data['del_chk']) or 'N',
                'insert_id': safe_str(data['insert_id']),
            }
        )
        # auto_now_add 필드 덮어쓰기
        if insert_dt:
            Enrollment.objects.filter(id=no_seq).update(insert_dt=insert_dt)
        count += 1

    print(f'Enrollment: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_enrollment_bills(cursor):
    """lf_fcjoin_bill → EnrollmentBill"""
    cursor.execute("""
        SELECT no_seq, bill_code, bill_desc, bill_amt,
               pay_stats, insert_id, insert_dt
          FROM lf_fcjoin_bill
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    valid_enrollment_ids = set(Enrollment.objects.values_list('id', flat=True))

    for row in rows:
        data = dict(zip(columns, row))
        no_seq = checkint(data['no_seq'])

        if no_seq not in valid_enrollment_ids:
            skipped += 1
            continue

        insert_dt = make_aware(data['insert_dt'])

        bill = EnrollmentBill.objects.create(
            enrollment_id=no_seq,
            bill_code=safe_str(data['bill_code']),
            bill_desc=safe_str(data['bill_desc']),
            bill_amt=checkint(data['bill_amt']),
            pay_stats=safe_str(data['pay_stats']) or 'UN',
            insert_id=safe_str(data['insert_id']),
        )
        if insert_dt:
            EnrollmentBill.objects.filter(id=bill.id).update(insert_dt=insert_dt)
        count += 1

    print(f'EnrollmentBill: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_enrollment_courses(cursor):
    """lf_fcjoin_course → EnrollmentCourse"""
    cursor.execute("""
        SELECT no_seq, bill_code, course_ym, course_ym_amt,
               lecture_code, start_ymd, course_stats
          FROM lf_fcjoin_course
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    valid_enrollment_ids = set(Enrollment.objects.values_list('id', flat=True))

    for row in rows:
        data = dict(zip(columns, row))
        no_seq = checkint(data['no_seq'])

        if no_seq not in valid_enrollment_ids:
            skipped += 1
            continue

        course_ym = safe_date(data['course_ym'])
        start_ymd = safe_date(data['start_ymd'])

        if course_ym is None:
            skipped += 1
            continue

        EnrollmentCourse.objects.create(
            enrollment_id=no_seq,
            bill_code=safe_str(data['bill_code']),
            course_ym=course_ym,
            course_ym_amt=checkint(data['course_ym_amt']),
            lecture_code=checkint(data['lecture_code']),
            start_ymd=start_ymd,
            course_stats=safe_str(data['course_stats']) or 'LY',
        )
        count += 1

    print(f'EnrollmentCourse: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_wait_students(cursor):
    """lf_wait_student → WaitStudent"""
    cursor.execute("""
        SELECT locd_code, sta_code, lecture_code,
               member_id, member_name, child_id, child_name,
               wait_seq, trans_gbn, del_chk, insert_id
          FROM lf_wait_student
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))

        WaitStudent.objects.create(
            local_code=checkint(data['locd_code']),
            sta_code=checkint(data['sta_code']),
            lecture_code=checkint(data['lecture_code']),
            member_id=safe_str(data['member_id']),
            member_name=safe_str(data['member_name']),
            child_id=safe_str(data['child_id']),
            child_name=safe_str(data['child_name']),
            wait_seq=checkint(data['wait_seq']),
            trans_gbn=safe_str(data['trans_gbn']) or 'N',
            del_chk=safe_str(data['del_chk']) or 'N',
            insert_id=safe_str(data['insert_id']),
        )
        count += 1

    print(f'WaitStudent: {count}건 이관 완료')


def migrate_payment_kcp(cursor):
    """lf_pay_kcp_log → PaymentKCP (성공 기록)"""
    cursor.execute("""
        SELECT req_tx, use_pay_method, bsucc, res_cd, res_msg,
               res_msg_bsucc, amount, ordr_idxx, tno,
               good_mny, good_name, buyr_name, buyr_tel1, buyr_tel2,
               buyr_mail, app_time, card_cd, card_name, app_no,
               noinf, quota, bank_name, bank_code, depositor,
               account, va_date, pay_seq, member_num, pg_gbn,
               add_pnt, use_pnt, rsv_pnt, insert_dt
          FROM lf_pay_kcp_log
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        insert_dt = make_aware(data['insert_dt'])

        obj = PaymentKCP.objects.create(
            req_tx=safe_str(data['req_tx']),
            use_pay_method=safe_str(data['use_pay_method']),
            bsucc=safe_str(data.get('bsucc', '')),
            res_cd=safe_str(data['res_cd']),
            res_msg=safe_str(data['res_msg']),
            res_msg_bsucc=safe_str(data.get('res_msg_bsucc', '')),
            amount=checkint(data['amount']),
            ordr_idxx=safe_str(data['ordr_idxx']),
            tno=safe_str(data['tno']),
            good_mny=checkint(data['good_mny']),
            good_name=safe_str(data['good_name']),
            buyr_name=safe_str(data['buyr_name']),
            buyr_tel1=safe_str(data['buyr_tel1']),
            buyr_tel2=safe_str(data['buyr_tel2']),
            buyr_mail=safe_str(data['buyr_mail']),
            app_time=safe_str(data['app_time']),
            card_cd=safe_str(data['card_cd']),
            card_name=safe_str(data['card_name']),
            app_no=safe_str(data['app_no']),
            noinf=safe_str(data['noinf']),
            quota=safe_str(data['quota']),
            bank_name=safe_str(data['bank_name']),
            bank_code=safe_str(data['bank_code']),
            depositor=safe_str(data['depositor']),
            account=safe_str(data['account']),
            va_date=safe_str(data['va_date']),
            pay_seq=checkint(data['pay_seq']),
            member_num=safe_str(data['member_num']),
            pg_gbn=safe_str(data.get('pg_gbn', 'KCP')),
            add_pnt=checkint(data.get('add_pnt', 0)),
            use_pnt=checkint(data.get('use_pnt', 0)),
            rsv_pnt=checkint(data.get('rsv_pnt', 0)),
        )
        if insert_dt:
            PaymentKCP.objects.filter(id=obj.id).update(insert_dt=insert_dt)
        count += 1

    print(f'PaymentKCP: {count}건 이관 완료')


def migrate_payment_fails(cursor):
    """lf_pay_kcp_faillog → PaymentFail"""
    try:
        cursor.execute("""
            SELECT req_tx, use_pay_method, res_cd, res_msg,
                   amount, ordr_idxx, good_name, buyr_name,
                   member_num, insert_dt
              FROM lf_pay_kcp_faillog
        """)
    except pyodbc.ProgrammingError:
        print('PaymentFail: lf_pay_kcp_faillog 테이블 없음 - 스킵')
        return

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        insert_dt = make_aware(data['insert_dt'])

        obj = PaymentFail.objects.create(
            req_tx=safe_str(data['req_tx']),
            use_pay_method=safe_str(data['use_pay_method']),
            res_cd=safe_str(data['res_cd']),
            res_msg=safe_str(data['res_msg']),
            amount=checkint(data['amount']),
            ordr_idxx=safe_str(data['ordr_idxx']),
            good_name=safe_str(data['good_name']),
            buyr_name=safe_str(data['buyr_name']),
            member_num=safe_str(data['member_num']),
        )
        if insert_dt:
            PaymentFail.objects.filter(id=obj.id).update(insert_dt=insert_dt)
        count += 1

    print(f'PaymentFail: {count}건 이관 완료')


def main():
    print('MSSQL → PostgreSQL 수강신청/결제 데이터 이관 시작...')
    print('=' * 50)

    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    # 의존성 순서대로 이관
    migrate_lecture_seldays(cursor)
    migrate_promotion_members(cursor)
    migrate_enrollments(cursor)
    migrate_enrollment_bills(cursor)
    migrate_enrollment_courses(cursor)
    migrate_wait_students(cursor)
    migrate_payment_kcp(cursor)
    migrate_payment_fails(cursor)

    conn.close()

    # 검증
    print(f'\n{"=" * 50}')
    print('=== 검증 ===')
    print(f'LectureSelDay 총 건수: {LectureSelDay.objects.count()}')
    print(f'PromotionMember 총 건수: {PromotionMember.objects.count()}')
    print(f'Enrollment 총 건수: {Enrollment.objects.count()}')
    print(f'EnrollmentBill 총 건수: {EnrollmentBill.objects.count()}')
    print(f'EnrollmentCourse 총 건수: {EnrollmentCourse.objects.count()}')
    print(f'WaitStudent 총 건수: {WaitStudent.objects.count()}')
    print(f'PaymentKCP 총 건수: {PaymentKCP.objects.count()}')
    print(f'PaymentFail 총 건수: {PaymentFail.objects.count()}')


if __name__ == '__main__':
    main()
