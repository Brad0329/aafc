"""
MSSQL → PostgreSQL 공통 코드 데이터 이관 스크립트
실행: python manage.py shell < scripts/migrate_common.py
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
from apps.common.models import CodeGroup, CodeValue, Setting

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def migrate_codegroup(cursor):
    """lf_codegroup → CodeGroup"""
    cursor.execute('SELECT grpcode, grpcode_name, del_chk, insert_dt, insert_id FROM lf_codegroup')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        CodeGroup.objects.update_or_create(
            grpcode=row[0],
            defaults={
                'grpcode_name': row[1] or '',
                'del_chk': row[2] or 'N',
                'insert_dt': row[3],
                'insert_id': row[4] or '',
            }
        )
        count += 1
    print(f'CodeGroup: {count}건 이관 완료')


def migrate_codevalue(cursor):
    """lf_codesub → CodeValue"""
    cursor.execute('SELECT subcode, grpcode, code_name, code_desc, code_order, del_chk, insert_dt, insert_id, YARD_SEQ FROM lf_codesub')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        CodeValue.objects.update_or_create(
            subcode=row[0],
            group_id=row[1],
            defaults={
                'code_name': row[2] or '',
                'code_desc': row[3] or '',
                'code_order': row[4] or 0,
                'del_chk': row[5] or 'N',
                'insert_dt': row[6],
                'insert_id': row[7] or '',
                'yard_seq': row[8] or '',
            }
        )
        count += 1
    print(f'CodeValue: {count}건 이관 완료')


def migrate_setting(cursor):
    """lf_setting → Setting"""
    cursor.execute('SELECT idx, join_price, pk_price, insert_id, insert_dt FROM lf_setting')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        Setting.objects.update_or_create(
            id=row[0],
            defaults={
                'join_price': row[1],
                'pk_price': row[2],
                'insert_id': row[3] or '',
                'insert_dt': row[4],
            }
        )
        count += 1
    print(f'Setting: {count}건 이관 완료')


def main():
    print('MSSQL → PostgreSQL 공통 코드 이관 시작...')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    migrate_codegroup(cursor)
    migrate_codevalue(cursor)
    migrate_setting(cursor)

    conn.close()
    print('이관 완료!')


if __name__ == '__main__':
    main()
