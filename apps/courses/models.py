from django.db import models


class Stadium(models.Model):
    """구장 (lf_stadium)"""
    sta_code = models.IntegerField('구장코드', unique=True)
    local_code = models.IntegerField('권역코드', default=0)
    sta_name = models.CharField('구장명', max_length=100)
    sta_nickname = models.CharField('구장별칭', max_length=100, blank=True)
    sta_phone = models.CharField('연락처', max_length=50, blank=True)
    sta_address = models.CharField('주소', max_length=200, blank=True)
    sta_s_img = models.CharField('소이미지', max_length=200, blank=True)
    sta_l_img = models.CharField('대이미지', max_length=200, blank=True)
    sta_p_img = models.CharField('페이지이미지', max_length=200, blank=True)
    sta_m_img = models.CharField('모바일이미지', max_length=200, blank=True)
    sta_desc = models.TextField('소개', blank=True)
    sta_coach = models.CharField('담당코치', max_length=100, blank=True)
    use_gbn = models.CharField('사용여부', max_length=1, default='Y')
    kapa_tot = models.IntegerField('총정원', default=0)
    inve = models.CharField('투자구분', max_length=10, blank=True)
    grou = models.CharField('그룹구분', max_length=10, blank=True)
    three_lecyn = models.CharField('3회체험여부', max_length=1, blank=True)
    order_seq = models.IntegerField('정렬순서', default=0)
    location_url = models.TextField('지도URL', blank=True)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'courses_stadium'
        verbose_name = '구장'
        verbose_name_plural = '구장'
        ordering = ['order_seq', 'sta_name']

    def __str__(self):
        return self.sta_name


class Coach(models.Model):
    """코치 (lf_coach)"""
    coach_code = models.IntegerField('코치코드', unique=True)
    coach_name = models.CharField('코치명', max_length=60)
    coach_level = models.CharField('직급', max_length=10, blank=True)
    phone = models.CharField('연락처', max_length=14, blank=True)
    dpart = models.CharField('부서', max_length=40, blank=True)
    coach_s_img = models.CharField('이미지', max_length=200, blank=True)
    use_gbn = models.CharField('사용여부', max_length=1, default='Y')
    order_seq = models.IntegerField('정렬순서', default=0)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'courses_coach'
        verbose_name = '코치'
        verbose_name_plural = '코치'
        ordering = ['order_seq', 'coach_name']

    def __str__(self):
        return self.coach_name


class StadiumCoach(models.Model):
    """구장-코치 매핑 (lf_stacoach)"""
    stadium = models.ForeignKey(
        Stadium, on_delete=models.CASCADE,
        related_name='stadium_coaches',
        db_column='stadium_id',
        verbose_name='구장'
    )
    coach = models.ForeignKey(
        Coach, on_delete=models.CASCADE,
        related_name='coach_stadiums',
        db_column='coach_id',
        verbose_name='코치'
    )

    class Meta:
        db_table = 'courses_stadiumcoach'
        verbose_name = '구장-코치'
        verbose_name_plural = '구장-코치'
        unique_together = ['stadium', 'coach']

    def __str__(self):
        return f'{self.stadium} - {self.coach}'


class Lecture(models.Model):
    """강좌 (lf_lecture)"""
    lecture_code = models.IntegerField('강좌코드', unique=True)
    local_code = models.IntegerField('권역코드', default=0)
    stadium = models.ForeignKey(
        Stadium, on_delete=models.CASCADE,
        related_name='lectures',
        verbose_name='구장',
        null=True, blank=True
    )
    lecture_title = models.CharField('강좌명', max_length=100, blank=True)
    lec_age = models.CharField('대상', max_length=40, blank=True)
    lecture_day = models.IntegerField('요일', default=0)  # 1~7 (월~일)
    lecture_time = models.CharField('시간', max_length=10, blank=True)
    class_gbn = models.CharField('클래스구분', max_length=5, blank=True)  # A/B/C/D
    class_gbn2 = models.CharField('반구분', max_length=5, blank=True)  # N=취미/P=프로
    lec_price = models.IntegerField('수강료', default=0)
    stu_cnt = models.IntegerField('정원', default=0)
    coach = models.ForeignKey(
        Coach, on_delete=models.SET_NULL,
        related_name='lectures_as_coach',
        verbose_name='담당코치',
        null=True, blank=True
    )
    t_coach = models.ForeignKey(
        Coach, on_delete=models.SET_NULL,
        related_name='lectures_as_tcoach',
        verbose_name='수업코치',
        null=True, blank=True
    )
    sub_coach = models.CharField('보조코치', max_length=60, blank=True)
    dc_2 = models.IntegerField('주2회할인', default=0)
    dc_3 = models.IntegerField('주3회할인', default=0)
    dc_4 = models.IntegerField('주4회할인', default=0)
    use_gbn = models.CharField('사용여부', max_length=1, default='Y')
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'courses_lecture'
        verbose_name = '강좌'
        verbose_name_plural = '강좌'

    def __str__(self):
        return self.lecture_title or f'강좌 {self.lecture_code}'

    def get_day_display(self):
        days = {1: '월', 2: '화', 3: '수', 4: '목', 5: '금', 6: '토', 7: '일'}
        return days.get(self.lecture_day, '')


class StadiumGoal(models.Model):
    """구장 목표 (lf_stadium_goal)"""
    stadium = models.ForeignKey(
        Stadium, on_delete=models.CASCADE,
        related_name='goals',
        verbose_name='구장'
    )
    sta_year = models.IntegerField('연도')
    sta_month = models.CharField('월', max_length=2)
    sta_goal = models.IntegerField('목표인원', default=0)

    class Meta:
        db_table = 'courses_stadiumgoal'
        verbose_name = '구장목표'
        verbose_name_plural = '구장목표'

    def __str__(self):
        return f'{self.stadium} {self.sta_year}-{self.sta_month}'


class Promotion(models.Model):
    """프로모션 (lf_promotion)"""
    uid = models.IntegerField('프로모션ID', unique=True)
    kind = models.CharField('종류', max_length=20, blank=True)
    title = models.CharField('제목', max_length=200, blank=True)
    summary = models.CharField('요약', max_length=500, blank=True)
    start_date = models.DateTimeField('시작일', null=True, blank=True)
    end_date = models.DateTimeField('종료일', null=True, blank=True)
    discount = models.IntegerField('할인액', default=0)
    discount_unit = models.CharField('할인단위', max_length=5, blank=True)  # 1=원, 2=%
    is_price_limit = models.CharField('금액제한여부', max_length=5, blank=True)  # T/F
    min_price = models.IntegerField('최소금액', default=0)
    max_price = models.IntegerField('최대금액', default=0)
    issue_mode = models.IntegerField('발급모드', default=0)  # 1=회원별, 2=야드별, 3=구장별
    use_mode = models.IntegerField('사용모드', default=0)  # 1=교육용품비, 2=수강료, 3=결제금액
    is_use = models.CharField('사용여부', max_length=5, default='T')  # T/F
    local_code = models.IntegerField('권역코드', null=True, blank=True)
    sta_code = models.IntegerField('구장코드', null=True, blank=True)
    member_code = models.CharField('회원코드', max_length=30, blank=True)
    reg_date = models.DateTimeField('등록일', null=True, blank=True)

    class Meta:
        db_table = 'courses_promotion'
        verbose_name = '프로모션'
        verbose_name_plural = '프로모션'

    def __str__(self):
        return self.title or f'프로모션 {self.uid}'


class LectureSelDay(models.Model):
    """강좌별 수업일 스케줄 (lf_lecture_selday)"""
    lecture_code = models.IntegerField('강좌코드')
    syear = models.IntegerField('연도')
    smonth = models.IntegerField('월')
    sday = models.IntegerField('일')
    admin_id = models.CharField('등록자', max_length=30, blank=True)

    class Meta:
        db_table = 'courses_lectureselday'
        verbose_name = '수업일정'
        verbose_name_plural = '수업일정'
        unique_together = ['lecture_code', 'syear', 'smonth', 'sday']

    def __str__(self):
        return f'강좌{self.lecture_code} {self.syear}-{self.smonth:02d}-{self.sday:02d}'


class PromotionMember(models.Model):
    """프로모션-회원 매핑 (lf_promotion_member)"""
    coupon_uid = models.IntegerField('프로모션ID')
    member_id = models.CharField('회원아이디', max_length=30)
    child_id = models.CharField('자녀아이디', max_length=25)
    used = models.CharField('사용여부', max_length=1, default='T')
    is_trash = models.CharField('삭제여부', max_length=1, default='T')

    class Meta:
        db_table = 'courses_promotionmember'
        verbose_name = '프로모션회원'
        verbose_name_plural = '프로모션회원'

    def __str__(self):
        return f'프로모션{self.coupon_uid} - {self.member_id}/{self.child_id}'
