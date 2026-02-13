"""
MSSQL → PostgreSQL 강좌/구장/코치 데이터 이관 스크립트
실행: python scripts/migrate_courses.py
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
from apps.courses.models import (
    Stadium, Coach, StadiumCoach, Lecture, StadiumGoal, Promotion
)

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)

# ASP loadStadium.asp에서 추출한 구글맵 iframe src 매핑
LOCATION_MAP = {
    4: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.6272606455277!2d127.08538591583775!3d37.49312143608586!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca5cc179538f7%3A0xd7338229ad825607!2z7ISc7Jq47Yq567OE7IucIOqwleuCqOq1rCDsnbzsm5Drj5kg7JaR7J6s64yA66GcNTXquLggMjg!5e0!3m2!1sko!2skr!4v1547776586483",
    5: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d5319.412217742898!2d127.03107658849311!3d37.556443720860386!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca35e75f94e35%3A0x90a4fa63b825b507!2z7ISc7Jq47Yq567OE7IucIOyEseuPmeq1rCDtlonri7kx64-ZIOqzoOyCsOyekOuhnDjquLggNg!5e0!3m2!1sko!2skr!4v1547776678634",
    6: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3163.27286625327!2d127.09361611583894!3d37.54863453290999!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca532573c2fbb%3A0x4157f0862cadd63a!2z7ISc7Jq47Yq567OE7IucIOq0keynhOq1rCDqtazsnZjrj5kg7LKc7Zi464yA66GcIDczMQ!5e0!3m2!1sko!2skr!4v1547776702170",
    7: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d4473.727458791698!2d127.22088439469236!3d37.54556745249414!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357cb3d2021e0c6f%3A0xbf6f19bd4ac702bc!2z7Iqk7YOA7ZWE65OcIO2VmOuCqA!5e0!3m2!1sko!2skr!4v1547776758738",
    8: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.206290987642!2d127.0766620772151!3d37.50305241541481!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca44a14151867%3A0x31fdd1ca108d6218!2z7ISc7Jq47Yq567OE7IucIOyGoe2MjOq1rCDsnqDsi6Trs7jrj5kgMzA2!5e0!3m2!1sko!2skr!4v1547776796770",
    9: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.1424262277287!2d127.06602501583816!3d37.50455883543176!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca438ea78f1d5%3A0xe9bafe9d3f45bcc4!2z7ISc7Jq47Yq567OE7IucIOqwleuCqOq1rCDrjIDsuZjrj5kg7Jet7IK866GcMTA36ri4IDIwLTMw!5e0!3m2!1sko!2skr!4v1547776822810",
    10: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3161.7268211570217!2d126.91954991583961!3d37.58504993082437!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9850785af241%3A0x9d263a40fdd5f376!2z7ISc7Jq47Yq567OE7IucIOydgO2Pieq1rCDsnZHslZTrj5kg6rCA7KKM66GcNeq4uCA1!5e0!3m2!1sko!2skr!4v1547776863138",
    11: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3159.49697039465!2d126.91560171584052!3d37.63751872781659!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c97a3ac77e475%3A0xdcdb1d15e917c7b1!2z66Gv642w66qoIOydgO2PieijkA!5e0!3m2!1sko!2skr!4v1547776895037",
    12: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3161.7268211570217!2d126.91954991583961!3d37.58504993082437!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9850785af241%3A0x9d263a40fdd5f376!2z7ISc7Jq47Yq567OE7IucIOydgO2Pieq1rCDsnZHslZTrj5kg6rCA7KKM66GcNeq4uCA1!5e0!3m2!1sko!2skr!4v1547776863138",
    13: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d50528.46940761783!2d126.73293585490448!3d37.672018410920856!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9ac9cc2444bb%3A0x43c5f886673039cf!2z66Gc6rCA7ZKL7IK07Iqk7YOA65SU7JuA6rOg7JaR7YSw66-464SQ7KCQ!5e0!3m2!1sko!2skr!4v1676961550170!5m2!1sko!2skr",
    14: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3162.7346801159365!2d126.850952365839!3d37.561314332183755!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9c0eeb2ac3ad%3A0xd62813c716c13e98!2z7Jyg7ISd7LSI65Ox7ZWZ6rWQ!5e0!3m2!1sko!2skr!4v1547777009490",
    15: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3164.656613307528!2d126.85376141583828!3d37.516016334776566!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9dc4e00f2fdd%3A0xbfb30222e0c594a0!2z7ISc7Jq47Yq567OE7IucIOyWkeyynOq1rCDsi6DsoJXrj5kg7KSR7JWZ66GcIDIwNg!5e0!3m2!1sko!2skr!4v1547777034938",
    16: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.4095725641982!2d126.87054941532975!3d37.49825713579308!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9e0959ce720d%3A0x37cb8388b5f18f27!2z7ISc7Jq47Yq567OE7IucIOq1rOuhnOq1rCDqtazroZzrj5kg6rK97J2466GcIDQ4Mg!5e0!3m2!1sko!2skr!4v1584093700154!5m2!1sko!2skr",
    17: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.5920301075666!2d126.95816661583784!3d37.4939526360383!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca1d3e451bbe7%3A0x1e6b3a4a20839248!2z7ISc7Jq47Yq567OE7IucIOuPmeyekeq1rCDsg4Hrj4Trj5kg7IKs64u566GcMuq4uCAyLTE5!5e0!3m2!1sko!2skr!4v1547777111652",
    18: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.8711667980497!2d126.95817546583787!3d37.48736648641493!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca1d496d586fd%3A0x24115f92226b5c6c!2z6rSA7JWF7ZG466W07KeA7Jik!5e0!3m2!1sko!2skr!4v1547777175970",
    19: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.622301623097!2d126.91752281583788!3d37.49323843607908!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9fb050d2b793%3A0x3fdcb32dd253db61!2z7ISc7Jq47Yq567OE7IucIOuPmeyekeq1rCDsi6DrjIDrsKnrj5kgMzk1!5e0!3m2!1sko!2skr!4v1547777206364",
    20: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d791.4511970166827!2d126.8941826292445!3d37.48893276286595!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9e3c715d6a33%3A0xa3a3192fcc8658a6!2z7JiB7ISc7KSR7ZWZ6rWQ!5e0!3m2!1sko!2skr!4v1547777243215",
    21: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3160.2958365431614!2d127.05266071584008!3d37.61872842889407!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357cbb93988ec9ab%3A0xf31d8232942f6fe9!2z6rSR7Jq07TSI65Ox7ZWZ6rWQ!5e0!3m2!1sko!2skr!4v1547777271378",
    22: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3158.284058127824!2d127.05982421584076!3d37.666032626180446!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357cb9180d2981bf%3A0xda90199850bb2019!2z7ISc7Jq47Yq567OE7IucIOuFuOybkOq1rCDsg4Hqs4Q564-ZIO2VnOq4gOu5hOyEneuhnCA1MDY!5e0!3m2!1sko!2skr!4v1547777293993",
    23: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3159.8478019938498!2d127.08820411584007!3d37.62926772828965!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357cb9887e6602c9%3A0xd33717e2305c54ba!2z7ZmU656R7TSI65Ox7ZWZ6rWQ!5e0!3m2!1sko!2skr!4v1547777326908",
    24: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3160.7379528623705!2d126.81923591531283!3d37.6083258797901!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9b06c26a6909%3A0x3ffb8a39c2f89d2f!2z6rK96riw64-EIOqzoOyWkeyLnCDrjZXslpHqtawg7ZaJ7KO864K064-ZIDQ1NC0x!5e0!3m2!1sko!2skr!4v1557391703579!5m2!1sko!2skr",
    25: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d6338.23923401161!2d127.12489744754282!3d37.41064750668043!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca87537449601%3A0x377d09f9c4a929e0!2z6rK96riw64-EIOyEseuCqOyLnCDrtoTri7nqtawg7JW87YOR64-ZIOyVvO2DkeuhnDgx67KI6ri4IDEx!5e0!3m2!1sko!2skr!4v1556613989862!5m2!1sko!2skr",
    27: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3159.8478019938498!2d127.08820411584007!3d37.62926772828965!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357cb9887e6602c9%3A0xd33717e2305c54ba!2z7ZmU656R7TSI65Ox7ZWZ6rWQ!5e0!3m2!1sko!2skr!4v1547777326908",
    28: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3175.215995926476!2d127.03234701583413!3d37.26630484902186!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357b435a2afa15e7%3A0x358dbb04c430d34c!2z6rK96riw64-EIOyImOybkOyLnCDtjJTri6zqtawg7J246rOE64-ZIOyduOqzhOuhnCAxNTQ!5e0!3m2!1sko!2skr!4v1572324071147!5m2!1sko!2skr",
    29: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.409752974023!2d126.87054941530965!3d37.49825287981067!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9e0959ce720d%3A0x37cb8388b5f18f27!2z7ISc7Jq47Yq567OE7IucIOq1rOuhnOq1rCDqtazroZzrj5kg6rK97J2466GcIDQ4Mg!5e0!3m2!1sko!2skr!4v1583303967670!5m2!1sko!2skr",
    30: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1580.2253714203139!2d127.15288430830931!3d37.61508391960349!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357cb76e2d0c984f%3A0xf791ca869e2dca56!2z7ZiE64yA7ZSE66as66-47JeE7JWE7Jq466CbIOyKpO2OmOydtOyKpOybkA!5e0!3m2!1sko!2skr!4v1603945790100!5m2!1sko!2skr",
    32: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3170.824985435937!2d126.8061919157891!3d37.370317843097745!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357b65b1783e74bf%3A0x25f9a5311d7141a0!2z7Iuc7Z2lIOyepe2YhOyngOq1rCDtlIzrnpHrk5zrpbQ!5e0!3m2!1sko!2skr!4v1627878789114!5m2!1sko!2skr",
    33: "https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d12674.48289842753!2d126.88010272695311!3d37.42243862311072!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0xdd86f7057afc401e!2z66Gv642w66qoIOq0keuqhQ!5e0!3m2!1sko!2skr!4v1633581657688!5m2!1sko!2skr",
    34: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3164.9523562617787!2d126.87720531558715!3d37.50904183517589!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357c9e6fe5dae3bf%3A0x754286082b77389c!2z7ISc7Jq47Yq567OE7IucIOq1rOuhnOq1rCDsi6Drj4Trprzrj5kg7Iug64-E66a866GcMTHrgpjquLggOA!5e0!3m2!1sko!2skr!4v1633412138574!5m2!1sko!2skr",
    36: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3164.8593728637998!2d127.09583871531007!3d37.51123477980829!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca5a720cc0a33%3A0x635113229ddc0414!2z7ISc7Jq47Yq567OE7IucIOyGoe2MjOq1rCDsmKzrprztlL3roZwgMjQw!5e0!3m2!1sko!2skr!4v1652159586531!5m2!1sko!2skr",
    37: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3172.1347660505976!2d126.81371031558375!3d37.33931804486533!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357b6f986bf77b21%3A0x5ef990dccd8f2cfe!2z6rK96riw64-EIOyViOyCsOyLnCDri6jsm5Dqtawg64us66-466GcIDY0!5e0!3m2!1sko!2skr!4v1652056647945!5m2!1sko!2skr",
    39: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.198951991676!2d126.95800492637872!3d37.50322552775506!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357ca1dbfa59d291%3A0x645053f258fa1aef!2z7ISc7Jq47J2A66Gc7TSI65Ox7ZWZ6rWQ!5e0!3m2!1sko!2skr!4v1682558227177!5m2!1sko!2skr",
    40: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3169.9413513492573!2d126.91726307635571!3d37.39121923416093!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357b672d08afc5ff%3A0xb5fa94b8163069c5!2z6rK96riw64-EIOyViOyWkeyLnCDrp4zslYjqtawg7IKs64u566GcMzfrsojquLggMjI!5e0!3m2!1sko!2skr!4v1692766336057!5m2!1sko!2skr",
    41: "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3165.53355017184!2d127.13781357629418!3d37.495332328207056!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x357caf76f3907b39%3A0x28bb797f199d3057!2z7YOc7Iq57LaV6rWs7JWE7Lm0642w66-4!5e0!3m2!1sko!2sus!4v1753765710854!5m2!1sko!2sus",
}


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


def migrate_stadiums(cursor):
    """lf_stadium → Stadium"""
    cursor.execute("""
        SELECT sta_code, local_code, sta_name, sta_nickname,
               sta_phone, sta_address, sta_s_img, sta_l_img,
               sta_p_img, sta_m_img, sta_desc, sta_coach,
               use_gbn, kapa_tot, inve, grou, three_lecyn,
               order_seq, insert_dt
          FROM lf_stadium
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        sta_code = checkint(data['sta_code'])

        Stadium.objects.update_or_create(
            sta_code=sta_code,
            defaults={
                'local_code': checkint(data['local_code']),
                'sta_name': safe_str(data['sta_name']),
                'sta_nickname': safe_str(data['sta_nickname']),
                'sta_phone': safe_str(data['sta_phone']),
                'sta_address': safe_str(data['sta_address']),
                'sta_s_img': safe_str(data['sta_s_img']),
                'sta_l_img': safe_str(data['sta_l_img']),
                'sta_p_img': safe_str(data['sta_p_img']),
                'sta_m_img': safe_str(data['sta_m_img']),
                'sta_desc': safe_str(data['sta_desc']),
                'sta_coach': safe_str(data['sta_coach']),
                'use_gbn': safe_str(data['use_gbn']) or 'N',
                'kapa_tot': checkint(data['kapa_tot']),
                'inve': safe_str(data['inve']),
                'grou': safe_str(data['grou']),
                'three_lecyn': safe_str(data['three_lecyn']),
                'order_seq': checkint(data['order_seq']),
                'location_url': LOCATION_MAP.get(sta_code, ''),
                'insert_dt': make_aware(data['insert_dt']),
            }
        )
        count += 1

    print(f'Stadium: {count}건 이관 완료')


def migrate_coaches(cursor):
    """lf_coach → Coach"""
    cursor.execute("""
        SELECT coach_code, coach_name, coach_level,
               mhtel1, mhtel2, mhtel3, dpart, coach_s_img,
               use_gbn, order_seq, insert_dt
          FROM lf_coach
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        Coach.objects.update_or_create(
            coach_code=checkint(data['coach_code']),
            defaults={
                'coach_name': safe_str(data['coach_name']),
                'coach_level': safe_str(data['coach_level']),
                'phone': combine_phone(data['mhtel1'], data['mhtel2'], data['mhtel3']),
                'dpart': safe_str(data['dpart']),
                'coach_s_img': safe_str(data['coach_s_img']),
                'use_gbn': safe_str(data['use_gbn']) or 'N',
                'order_seq': checkint(data['order_seq']),
                'insert_dt': make_aware(data['insert_dt']),
            }
        )
        count += 1

    print(f'Coach: {count}건 이관 완료')


def migrate_stadium_coaches(cursor):
    """lf_stacoach → StadiumCoach"""
    cursor.execute('SELECT sta_code, coach_code FROM lf_stacoach')
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    for row in rows:
        sta_code = checkint(row[0])
        coach_code = checkint(row[1])

        try:
            stadium = Stadium.objects.get(sta_code=sta_code)
            coach = Coach.objects.get(coach_code=coach_code)
        except (Stadium.DoesNotExist, Coach.DoesNotExist):
            skipped += 1
            continue

        StadiumCoach.objects.update_or_create(
            stadium=stadium,
            coach=coach,
        )
        count += 1

    print(f'StadiumCoach: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_lectures(cursor):
    """lf_lecture → Lecture"""
    cursor.execute("""
        SELECT lecture_code, local_code, sta_code, lecture_title,
               lec_age, lecture_day, lecture_time, class_gbn,
               class_gbn2, lec_price, stu_cnt, coach_code,
               t_coach_code, sub_coach, dc_2, dc_3, dc_4,
               use_gbn, insert_dt
          FROM lf_lecture
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        sta_code = checkint(data['sta_code'])
        coach_code = checkint(data['coach_code'])
        t_coach_code = checkint(data['t_coach_code'])

        stadium = None
        if sta_code:
            stadium = Stadium.objects.filter(sta_code=sta_code).first()

        coach = None
        if coach_code:
            coach = Coach.objects.filter(coach_code=coach_code).first()

        t_coach = None
        if t_coach_code:
            t_coach = Coach.objects.filter(coach_code=t_coach_code).first()

        Lecture.objects.update_or_create(
            lecture_code=checkint(data['lecture_code']),
            defaults={
                'local_code': checkint(data['local_code']),
                'stadium': stadium,
                'lecture_title': safe_str(data['lecture_title']),
                'lec_age': safe_str(data['lec_age']),
                'lecture_day': checkint(data['lecture_day']),
                'lecture_time': safe_str(data['lecture_time']),
                'class_gbn': safe_str(data['class_gbn']),
                'class_gbn2': safe_str(data['class_gbn2']),
                'lec_price': checkint(data['lec_price']),
                'stu_cnt': checkint(data['stu_cnt']),
                'coach': coach,
                't_coach': t_coach,
                'sub_coach': safe_str(data['sub_coach']),
                'dc_2': checkint(data['dc_2']),
                'dc_3': checkint(data['dc_3']),
                'dc_4': checkint(data['dc_4']),
                'use_gbn': safe_str(data['use_gbn']) or 'N',
                'insert_dt': make_aware(data['insert_dt']),
            }
        )
        count += 1

    print(f'Lecture: {count}건 이관 완료')


def migrate_stadium_goals(cursor):
    """lf_stadium_goal → StadiumGoal"""
    cursor.execute('SELECT no_seq, sta_code, sta_year, sta_month, sta_goal FROM lf_stadium_goal')
    rows = cursor.fetchall()
    count = 0
    skipped = 0

    for row in rows:
        sta_code = checkint(row[1])
        stadium = Stadium.objects.filter(sta_code=sta_code).first()
        if not stadium:
            skipped += 1
            continue

        StadiumGoal.objects.update_or_create(
            id=checkint(row[0]),
            defaults={
                'stadium': stadium,
                'sta_year': checkint(row[2]),
                'sta_month': safe_str(row[3]),
                'sta_goal': checkint(row[4]),
            }
        )
        count += 1

    print(f'StadiumGoal: {count}건 이관 완료 (스킵: {skipped}건)')


def migrate_promotions(cursor):
    """lf_promotion → Promotion"""
    cursor.execute("""
        SELECT Uid, Kind, Title, Summary, StartDate, EndDate,
               Discount, DiscountUnit, IsPriceLimit, MinPrice, MaxPrice,
               IssueMode, UseMode, IsUse, local_code, sta_code,
               member_code, RegDate
          FROM lf_promotion
    """)
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    count = 0

    for row in rows:
        data = dict(zip(columns, row))
        Promotion.objects.update_or_create(
            uid=checkint(data['Uid']),
            defaults={
                'kind': safe_str(data['Kind']),
                'title': safe_str(data['Title']),
                'summary': safe_str(data['Summary']),
                'start_date': make_aware(data['StartDate']),
                'end_date': make_aware(data['EndDate']),
                'discount': checkint(data['Discount']),
                'discount_unit': safe_str(data['DiscountUnit']),
                'is_price_limit': safe_str(data['IsPriceLimit']),
                'min_price': checkint(data['MinPrice']),
                'max_price': checkint(data['MaxPrice']),
                'issue_mode': checkint(data['IssueMode']),
                'use_mode': checkint(data['UseMode']),
                'is_use': safe_str(data['IsUse']) or 'F',
                'local_code': checkint(data['local_code']) or None,
                'sta_code': checkint(data['sta_code']) or None,
                'member_code': safe_str(data['member_code']),
                'reg_date': make_aware(data['RegDate']),
            }
        )
        count += 1

    print(f'Promotion: {count}건 이관 완료')


def main():
    print('MSSQL → PostgreSQL 강좌/구장/코치 데이터 이관 시작...')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    migrate_stadiums(cursor)
    migrate_coaches(cursor)
    migrate_stadium_coaches(cursor)
    migrate_lectures(cursor)
    migrate_stadium_goals(cursor)
    migrate_promotions(cursor)

    conn.close()

    # 검증
    print(f'\n=== 검증 ===')
    print(f'Stadium 총 건수: {Stadium.objects.count()}')
    print(f'Coach 총 건수: {Coach.objects.count()}')
    print(f'StadiumCoach 총 건수: {StadiumCoach.objects.count()}')
    print(f'Lecture 총 건수: {Lecture.objects.count()}')
    print(f'StadiumGoal 총 건수: {StadiumGoal.objects.count()}')
    print(f'Promotion 총 건수: {Promotion.objects.count()}')


if __name__ == '__main__':
    main()
