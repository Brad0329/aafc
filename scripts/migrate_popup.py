"""
MSSQL → PostgreSQL 팝업 데이터 이관 스크립트
실행: python scripts/migrate_popup.py
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
from apps.board.models import Popup

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


def migrate_popup(cursor):
    """lf_popup → Popup"""
    cursor.execute('''
        SELECT no_seq, pop_title, pop_beginDate, pop_endDate,
               pop_img, pop_url, pop_width, pop_height,
               pop_left, pop_top, pop_urltype, pop_gbn,
               pop_yn, insert_dt, insert_id
        FROM lf_popup
        ORDER BY no_seq
    ''')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        no_seq = row[0]
        Popup.objects.update_or_create(
            id=no_seq,
            defaults={
                'pop_title': safe_str(row[1]),
                'pop_begin_date': safe_str(row[2]),
                'pop_end_date': safe_str(row[3]),
                'pop_img': safe_str(row[4]),
                'pop_url': safe_str(row[5]),
                'pop_width': safe_str(row[6]),
                'pop_height': safe_str(row[7]),
                'pop_left': safe_str(row[8]),
                'pop_top': safe_str(row[9]),
                'pop_urltype': safe_str(row[10]) or 'I',
                'pop_gbn': safe_str(row[11]) or 'P',
                'pop_yn': safe_str(row[12]) or 'Y',
                'insert_id': safe_str(row[14]),
            }
        )
        count += 1
    print(f'  Popup: {count}건 이관 완료')


if __name__ == '__main__':
    print('=== Popup 데이터 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    try:
        migrate_popup(cursor)
    except Exception as e:
        print(f'에러 발생: {e}')
    finally:
        cursor.close()
        conn.close()

    print('=== Popup 데이터 이관 완료 ===')
