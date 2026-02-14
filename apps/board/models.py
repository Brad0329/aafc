from django.db import models


class Board(models.Model):
    """게시판 (lf_board)"""
    b_seq = models.IntegerField('게시글번호', unique=True)
    b_ref = models.IntegerField('답글그룹번호', default=0)
    b_level = models.IntegerField('답글깊이', default=0)
    b_step = models.IntegerField('답글순서', default=0)
    b_gbn = models.CharField('게시판구분', max_length=3)
    b_notice_yn = models.CharField('공지여부', max_length=1, default='N')
    b_title = models.CharField('제목', max_length=200)
    b_content = models.TextField('내용', blank=True)
    b_hit = models.IntegerField('조회수', default=0)
    b_commend = models.IntegerField('추천수', default=0)
    insert_name = models.CharField('작성자명', max_length=20, blank=True)
    insert_id = models.CharField('작성자ID', max_length=12, blank=True)
    insert_type = models.CharField('작성자타입', max_length=1, blank=True)
    insert_dt = models.CharField('작성일', max_length=20, blank=True)
    insert_ip = models.CharField('IP주소', max_length=15, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')

    class Meta:
        db_table = 'board_board'
        verbose_name = '게시글'
        verbose_name_plural = '게시글'
        ordering = ['-b_seq']

    def __str__(self):
        return f'[{self.b_gbn}] {self.b_title}'


class BoardComment(models.Model):
    """게시판 댓글 (lf_boardcomment)"""
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='게시글',
        to_field='b_seq'
    )
    b_gbn = models.CharField('게시판구분', max_length=3, blank=True)
    comment = models.TextField('댓글내용')
    insert_name = models.CharField('작성자명', max_length=20, blank=True)
    insert_id = models.CharField('작성자ID', max_length=20, blank=True)
    insert_type = models.CharField('작성자타입', max_length=1, blank=True)
    insert_dt = models.DateTimeField('작성일', null=True, blank=True)
    insert_ip = models.CharField('IP주소', max_length=15, blank=True)
    del_chk = models.CharField('삭제여부', max_length=1, default='N')

    class Meta:
        db_table = 'board_boardcomment'
        verbose_name = '댓글'
        verbose_name_plural = '댓글'
        ordering = ['id']

    def __str__(self):
        return f'댓글: {self.comment[:30]}'


class BoardFile(models.Model):
    """게시판 첨부파일 (lf_boardsub)"""
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE,
        related_name='files',
        verbose_name='게시글',
        to_field='b_seq'
    )
    bs_img = models.CharField('이미지파일', max_length=300, blank=True)
    bs_thumimg = models.CharField('썸네일', max_length=300, blank=True)
    bs_file = models.CharField('첨부파일', max_length=300, blank=True)
    bs_downcnt = models.IntegerField('다운로드수', default=0)
    bs_no = models.IntegerField('순번', default=0)
    insert_dt = models.DateTimeField('등록일', null=True, blank=True)
    insert_id = models.CharField('등록자ID', max_length=12, blank=True)
    daum_uploadhost = models.CharField('Daum호스트', max_length=255, blank=True)
    daum_vid = models.CharField('Daum VID', max_length=128, blank=True)
    daum_thimg = models.CharField('Daum썸네일', max_length=255, blank=True)
    daum_width = models.CharField('Daum너비', max_length=4, blank=True)
    daum_height = models.CharField('Daum높이', max_length=4, blank=True)

    class Meta:
        db_table = 'board_boardfile'
        verbose_name = '첨부파일'
        verbose_name_plural = '첨부파일'
        ordering = ['bs_no']

    def __str__(self):
        return self.bs_img or self.bs_file or f'파일 {self.id}'
