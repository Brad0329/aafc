"""
MSSQL → PostgreSQL 회원 데이터 이관 스크립트
실행: python scripts/migrate_members.py
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
from apps.accounts.models import Member, MemberChild, OutMember

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


def combine_phone(p1, p2, p3):
    """전화번호 3분할 → 하이픈 결합"""
    parts = [p or '' for p in (p1, p2, p3)]
    if any(parts):
        return '-'.join(parts)
    return ''


def migrate_members(cursor):
    """lf_member → Member"""
    cursor.execute('SELECT * FROM lf_member ORDER BY member_code')
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    for row in rows:
        data = dict(zip(columns, row))
        member_id = (data['member_id'] or '').strip()
        if not member_id:
            skipped += 1
            continue

        Member.objects.update_or_create(
            username=member_id,
            defaults={
                'password': f"sha256${data['member_pwd']}" if data['member_pwd'] else '',
                'email': data['member_mail'] or '',
                'member_code': data['member_code'],
                'name': data['member_name'] or '',
                'tel': combine_phone(data['mtel1'], data['mtel2'], data['mtel3']),
                'phone': combine_phone(data['mhtel1'], data['mhtel2'], data['mhtel3']),
                'zipcode': data['zipcode'] or '',
                'address1': data['address1'] or '',
                'address2': data['address2'] or '',
                'sms_consent': data['smsyn'] or 'N',
                'mail_consent': data['mailyn'] or 'N',
                'status': data['member_status'] or 'N',
                'login_count': data['login_cnt'] or 0,
                'failed_count': data['failed_cnt'] or 0,
                'join_ncsafe': data['join_ncsafe'] or '',
                'birth': data['join_birth'] or '',
                'gender': data['join_sexgbn'] or '',
                'join_safe_di': data['join_safe_di'] or '',
                'join_ipin_key': data['join_ipin_key'] or '',
                'join_safegbn': data['join_safegbn'] or '',
                'last_login': make_aware(data['lastlogin_dt']),
                'secession_desc': data['secession_desc'] or '',
                'insert_dt': make_aware(data['insert_dt']),
                'join_path': data['join_path'] or '',
                'is_active': data['member_status'] != 'D',
            }
        )
        count += 1

    print(f'Member: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_children(cursor):
    """lf_memberchild → MemberChild"""
    cursor.execute('SELECT * FROM lf_memberchild ORDER BY child_code')
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    for row in rows:
        data = dict(zip(columns, row))
        member_id = (data['member_id'] or '').strip()
        if not member_id:
            skipped += 1
            continue

        # 부모 회원이 존재하는지 확인
        if not Member.objects.filter(username=member_id).exists():
            skipped += 1
            continue

        MemberChild.objects.update_or_create(
            child_code=data['child_code'],
            defaults={
                'parent_id': member_id,
                'name': data['child_name'] or '',
                'child_id': data['child_id'] or '',
                'child_pwd': data['child_pwd'] or '',
                'birth': data['child_birth'] or '',
                'gender': data['child_sexgbn'] or '',
                'school': data['sch_name'] or '',
                'grade': data['sch_grade'] or '',
                'height': data['child_height'] or '',
                'weight': data['child_weight'] or '',
                'size': data['child_size'] or '',
                'phone': combine_phone(data['chtel1'], data['chtel2'], data['chtel3']),
                'login_count': data['login_cnt'] or 0,
                'status': data['child_status'] or 'N',
                'last_login': make_aware(data['lastlogin_dt']),
                'secession_desc': data['secession_desc'] or '',
                'insert_dt': make_aware(data['insert_dt']),
                'join_path': data['join_path'] or '',
                'card_num': data['Card_num'] or '',
                'course_state': data['course_state'] or '',
            }
        )
        count += 1

    print(f'MemberChild: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_outmembers(cursor):
    """lf_outmember → OutMember"""
    cursor.execute('SELECT * FROM lf_outmember ORDER BY no_seq')
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        OutMember.objects.update_or_create(
            id=data['no_seq'],
            defaults={
                'member_id': data['member_id'] or '',
                'member_name': data['member_name'] or '',
                'out_desc': data['out_desc'] or '',
                'out_dt': make_aware(data['out_dt']),
            }
        )
        count += 1

    print(f'OutMember: {count}건 이관 완료')


def main():
    print('MSSQL → PostgreSQL 회원 데이터 이관 시작...')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    migrate_members(cursor)
    migrate_children(cursor)
    migrate_outmembers(cursor)

    conn.close()

    # 검증
    print(f'\n=== 검증 ===')
    print(f'Member 총 건수: {Member.objects.count()}')
    print(f'MemberChild 총 건수: {MemberChild.objects.count()}')
    print(f'OutMember 총 건수: {OutMember.objects.count()}')


if __name__ == '__main__':
    main()
