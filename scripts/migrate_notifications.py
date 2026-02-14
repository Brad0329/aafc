"""
MSSQL → PostgreSQL 알림 + SMS 데이터 이관 스크립트
실행: python scripts/migrate_notifications.py
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
from django.utils import timezone
from apps.notifications.models import Notification, OfficeNotification, SMSLog
from apps.accounts.models import Member

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def safe_str(val):
    if val is None:
        return ''
    return str(val).strip()


def checkint(val):
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def make_aware(dt):
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def migrate_notification():
    """lf_alim → Notification"""
    print('=== lf_alim → Notification 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_alim")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_alim: {total}건')

    Notification.objects.all().delete()
    print('기존 Notification 데이터 삭제')

    valid_members = set(Member.objects.values_list('username', flat=True))

    cursor.execute("""
        SELECT no_seq, alim_gbn, member_id, member_name, child_id,
               local_code, sta_code, lecture_code, alim_title, alim_content,
               alim_file, del_chk, insert_id, insert_name, insert_dt
        FROM lf_alim
        ORDER BY no_seq
    """)

    count = 0
    for row in cursor.fetchall():
        member_id = safe_str(row[2])
        if member_id and member_id not in valid_members:
            member_id = None

        Notification.objects.create(
            no_seq=checkint(row[0]),
            alim_gbn=safe_str(row[1]) or 'P',
            member_id=member_id or None,
            member_name=safe_str(row[3]),
            child_id=safe_str(row[4]),
            local_code=checkint(row[5]) or None,
            sta_code=checkint(row[6]) or None,
            lecture_code=checkint(row[7]) or None,
            alim_title=safe_str(row[8]),
            alim_content=safe_str(row[9]),
            alim_file=safe_str(row[10]),
            del_chk=safe_str(row[11]) or 'N',
            insert_id=safe_str(row[12]),
            insert_name=safe_str(row[13]),
            insert_dt=make_aware(row[14]),
        )
        count += 1

    conn.close()
    print(f'Notification 이관 완료: {count}건')


def migrate_office_notification():
    """lf_office_alim → OfficeNotification"""
    print('\n=== lf_office_alim → OfficeNotification 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_office_alim")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_office_alim: {total}건')

    OfficeNotification.objects.all().delete()
    print('기존 OfficeNotification 데이터 삭제')

    cursor.execute("""
        SELECT no_seq, atitle, acontent, del_chk, reg_dt, reg_id
        FROM lf_office_alim
        ORDER BY no_seq
    """)

    count = 0
    for row in cursor.fetchall():
        OfficeNotification.objects.create(
            no_seq=checkint(row[0]),
            atitle=safe_str(row[1]),
            acontent=safe_str(row[2]),
            del_chk=safe_str(row[3]) or 'N',
            reg_dt=make_aware(row[4]),
            reg_id=safe_str(row[5]),
        )
        count += 1

    conn.close()
    print(f'OfficeNotification 이관 완료: {count}건')


def migrate_sms_log():
    """em_mmt_tran_log_kyt → SMSLog"""
    print('\n=== em_mmt_tran_log_kyt → SMSLog 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM em_mmt_tran_log_kyt")
    total = cursor.fetchone()[0]
    print(f'MSSQL em_mmt_tran_log_kyt: {total}건')

    SMSLog.objects.all().delete()
    print('기존 SMSLog 데이터 삭제')

    cursor.execute("""
        SELECT mt_pr, mt_refkey, date_client_req, subject, content,
               callback, service_type, msg_status, recipient_num,
               broadcast_yn, date_mt_sent, date_rslt, mt_report_code_ib
        FROM em_mmt_tran_log_kyt
        ORDER BY mt_pr
    """)

    batch = []
    count = 0

    for row in cursor.fetchall():
        batch.append(SMSLog(
            msg_key=safe_str(row[1]),
            date_client_req=make_aware(row[2]),
            subject=safe_str(row[3]),
            content=safe_str(row[4]),
            callback=safe_str(row[5]),
            service_type=safe_str(row[6]).strip(),
            msg_status=safe_str(row[7]).strip(),
            recipient_num=safe_str(row[8]),
            broadcast_yn=safe_str(row[9]) or 'N',
            date_sent=make_aware(row[10]),
            date_rslt=make_aware(row[11]),
            rslt=safe_str(row[12]),
        ))

        if len(batch) >= 500:
            SMSLog.objects.bulk_create(batch)
            count += len(batch)
            batch = []
            if count % 10000 == 0:
                print(f'  진행: {count}/{total}건')

    if batch:
        SMSLog.objects.bulk_create(batch)
        count += len(batch)

    conn.close()
    print(f'SMSLog 이관 완료: {count}건')


if __name__ == '__main__':
    print('알림/SMS 데이터 마이그레이션 시작\n')
    migrate_notification()
    migrate_office_notification()
    migrate_sms_log()
    print('\n=== 최종 건수 확인 ===')
    print(f'Notification: {Notification.objects.count()}')
    print(f'OfficeNotification: {OfficeNotification.objects.count()}')
    print(f'SMSLog: {SMSLog.objects.count()}')
    print('\n알림/SMS 데이터 마이그레이션 완료!')
