from django.urls import path
from . import views
from . import views_report as rpt
from . import views_portal as portal

urlpatterns = [
    path('', views.main_view, name='office_main'),
    path('login/', views.login_view, name='office_login'),
    path('logout/', views.logout_view, name='office_logout'),

    # 시스템관리 > 관리자 관리
    path('manage/ofuser/', views.ofuser_list, name='office_ofuser_list'),
    path('manage/ofuser/write/', views.ofuser_write, name='office_ofuser_write'),
    path('manage/ofuser/modify/<int:pk>/', views.ofuser_modify, name='office_ofuser_modify'),
    path('manage/ofuser/del/<int:pk>/', views.ofuser_del, name='office_ofuser_del'),
    path('manage/ofuser/idcheck/', views.ofuser_idcheck, name='office_ofuser_idcheck'),

    # 시스템관리 > 코드 관리
    path('manage/code/', views.code_list, name='office_code_list'),
    path('manage/code/sub/', views.code_sub_list, name='office_code_sub_list'),
    path('manage/code/group/write/', views.codegroup_write, name='office_codegroup_write'),
    path('manage/code/group/modify/<str:pk>/', views.codegroup_modify, name='office_codegroup_modify'),
    path('manage/code/group/del/<str:pk>/', views.codegroup_del, name='office_codegroup_del'),
    path('manage/code/sub/write/', views.codesub_write, name='office_codesub_write'),
    path('manage/code/sub/modify/<str:grpcode>/<int:subcode>/', views.codesub_modify, name='office_codesub_modify'),
    path('manage/code/sub/del/', views.codesub_del, name='office_codesub_del'),

    # 시스템관리 > 포인트 설정
    path('manage/point/', views.point_setup, name='office_point_setup'),

    # 시스템관리 > 관리자 알림
    path('manage/alim/', views.office_alim_list, name='office_alim_list'),
    path('manage/alim/write/', views.office_alim_write, name='office_alim_write'),
    path('manage/alim/modify/<int:pk>/', views.office_alim_modify, name='office_alim_modify'),
    path('manage/alim/del/<int:pk>/', views.office_alim_del, name='office_alim_del'),

    # 회원관리 > 회원정보
    path('lfmember/member/', views.member_list, name='office_member_list'),
    path('lfmember/member/excel/', views.member_list_excel, name='office_member_list_excel'),
    path('lfmember/member/write/', views.member_write, name='office_member_write'),
    path('lfmember/member/modify/<str:member_id>/', views.member_modify, name='office_member_modify'),
    path('lfmember/member/idcheck/', views.member_idcheck, name='office_member_idcheck'),
    path('lfmember/member/childadd/<str:member_id>/', views.member_childadd, name='office_member_childadd'),

    # 회원관리 > 자녀정보
    path('lfmember/child/', views.child_list, name='office_child_list'),
    path('lfmember/child/modify/<str:child_id>/', views.child_modify, name='office_child_modify'),
    path('lfmember/child/detail/<str:child_id>/', views.child_detail, name='office_child_detail'),

    # 회원관리 > 회원통계
    path('lfmember/stat/', views.member_stat, name='office_member_stat'),

    # 회원관리 > SMS/LMS
    path('lfmember/sms/', views.sms_send, name='office_sms_send'),
    path('lfmember/sms/list/', views.sms_send_list, name='office_sms_send_list'),

    # 회원관리 > 회원포인트내역
    path('lfmember/point/', views.memberpoint_list, name='office_memberpoint_list'),
    path('lfmember/point/write/', views.memberpoint_write, name='office_memberpoint_write'),
    path('lfmember/point/del/<int:pk>/', views.memberpoint_del, name='office_memberpoint_del'),

    # 회원관리 > 탈퇴회원리스트
    path('lfmember/secession/', views.secession_list, name='office_secession_list'),

    # 상담관리 > 상담 리스트
    path('lfconsult/consult/', views.consult_list, name='office_consult_list'),
    path('lfconsult/consult/detail/<int:pk>/', views.consult_detail, name='office_consult_detail'),
    path('lfconsult/consult/input/', views.consult_input, name='office_consult_input'),

    # 상담관리 > 답변 관리
    path('lfconsult/answer/add/', views.consult_answer_add, name='office_consult_answer_add'),
    path('lfconsult/answer/edit/<int:pk>/', views.consult_answer_edit, name='office_consult_answer_edit'),
    path('lfconsult/answer/del/<int:pk>/', views.consult_answer_del, name='office_consult_answer_del'),

    # 상담관리 > AJAX
    path('lfconsult/ajax/stadium/', views.ajax_consult_stadium, name='office_ajax_consult_stadium'),
    path('lfconsult/ajax/coach/', views.ajax_consult_coach, name='office_ajax_consult_coach'),
    path('lfconsult/ajax/member-search/', views.ajax_consult_member_search, name='office_ajax_member_search'),
    path('lfconsult/ajax/child-list/', views.ajax_consult_child_list, name='office_ajax_child_list'),

    # 상담관리 > 권역설정
    path('lfconsult/local/', views.consult_local, name='office_consult_local'),
    path('lfconsult/local/write/', views.consult_local_write, name='office_consult_local_write'),
    path('lfconsult/local/modify/<int:pk>/', views.consult_local_modify, name='office_consult_local_modify'),
    path('lfconsult/local/del/<int:pk>/', views.consult_local_del, name='office_consult_local_del'),

    # 상담관리 > 무료체험
    path('lfconsult/free/', views.consult_free_list, name='office_consult_free'),
    path('lfconsult/free/confirm/<int:pk>/', views.consult_free_confirm, name='office_consult_free_confirm'),

    # 수강생관리 > AJAX
    path('lfstudent/ajax/local/', views.ajax_student_local, name='office_ajax_student_local'),
    path('lfstudent/ajax/stadium/', views.ajax_student_stadium, name='office_ajax_student_stadium'),
    path('lfstudent/ajax/course/', views.ajax_student_course, name='office_ajax_student_course'),

    # 수강생관리 > 기본금액관리
    path('lfstudent/dues/', views.dues_setting, name='office_dues_setting'),

    # 수강생관리 > 수강생정보
    path('lfstudent/student/', views.student_list, name='office_student_list'),

    # 수강생관리 > 수강생조회(이름검색)
    path('lfstudent/search/', views.student_search, name='office_student_search'),

    # 수강생관리 > 수강생상세
    path('lfstudent/student/detail/<int:no_seq>/', views.student_detail, name='office_student_detail'),
    path('lfstudent/student/shuttle-proc/', views.student_shuttle_proc, name='office_student_shuttle_proc'),
    path('lfstudent/student/alim-proc/', views.student_alim_proc, name='office_student_alim_proc'),

    # 수강생관리 > 입단신청내역
    path('lfstudent/master/', views.master_list, name='office_master_list'),
    path('lfstudent/master/detail/<int:no_seq>/', views.master_detail, name='office_master_detail'),
    path('lfstudent/master/excel/', views.master_list_excel, name='office_master_list_excel'),

    # 수강생관리 > 변경이력조회
    path('lfstudent/chghis/', views.chghis_list, name='office_chghis_list'),
    path('lfstudent/chghis/detail/<int:pk>/', views.chghis_detail, name='office_chghis_detail'),

    # 수강생관리 > 출결관리
    path('lfstudent/attendance/', views.attendance_view, name='office_attendance'),
    path('lfstudent/attendance/proc/', views.attendance_proc, name='office_attendance_proc'),

    # 수강생관리 > 대기정보관리
    path('lfstudent/wait/', views.wait_list, name='office_wait_list'),
    path('lfstudent/wait/write/', views.wait_write, name='office_wait_write'),
    path('lfstudent/wait/modify/<int:pk>/', views.wait_modify, name='office_wait_modify'),
    path('lfstudent/wait/delete/', views.wait_delete_proc, name='office_wait_delete'),

    # 수강생관리 > 클래식반관리 (개발준비중)
    path('lfstudent/classic/', views.under_development, {'page_title': '클래식반관리'}, name='office_classic_list'),

    # 수강생관리 > 수강생등록
    path('lfstudent/student/add/', views.student_add, name='office_student_add'),
    path('lfstudent/ajax/child-search/', views.ajax_child_search, name='office_ajax_child_search'),
    path('lfstudent/ajax/course-list/', views.ajax_course_list, name='office_ajax_course_list'),
    path('lfstudent/ajax/course-days/', views.ajax_course_days, name='office_ajax_course_days'),
    path('lfstudent/ajax/promotions/', views.ajax_promotions, name='office_ajax_promotions'),

    # 수강생관리 > 일괄처리
    path('lfstudent/batch/next-month/', views.batch_next_month_proc, name='office_batch_next_month'),
    path('lfstudent/batch/confirm/', views.batch_confirm_proc, name='office_batch_confirm'),
    path('lfstudent/batch/confirm-pay/', views.batch_confirm_pay_proc, name='office_batch_confirm_pay'),
    path('lfstudent/batch/lms/', views.batch_lms_proc, name='office_batch_lms'),

    # 과정관리 > 구장정보
    path('lfcourse/stadium/', views.stadium_list, name='office_stadium_list'),
    path('lfcourse/stadium/write/', views.stadium_write, name='office_stadium_write'),
    path('lfcourse/stadium/modify/<int:pk>/', views.stadium_modify, name='office_stadium_modify'),
    path('lfcourse/stadium/goal/<int:sta_code>/', views.stadium_goal, name='office_stadium_goal'),
    path('lfcourse/stadium/goal/del/<int:sta_code>/', views.stadium_goal_del, name='office_stadium_goal_delete'),

    # 과정관리 > 코칭스탭관리
    path('lfcourse/coach/', views.coach_list, name='office_coach_list'),
    path('lfcourse/coach/write/', views.coach_write, name='office_coach_write'),
    path('lfcourse/coach/modify/<int:pk>/', views.coach_modify, name='office_coach_modify'),
    path('lfcourse/coach/del/<int:pk>/', views.coach_del, name='office_coach_delete'),

    # 과정관리 > 과정관리(강좌)
    path('lfcourse/lecture/', views.lecture_list, name='office_lecture_list'),
    path('lfcourse/lecture/write/', views.lecture_write, name='office_lecture_write'),
    path('lfcourse/lecture/modify/<int:pk>/', views.lecture_modify, name='office_lecture_modify'),
    path('lfcourse/lecture/del/<int:pk>/', views.lecture_del, name='office_lecture_delete'),
    path('lfcourse/lecture/timetable/<int:lecture_code>/', views.lecture_timetable, name='office_lecture_timetable'),

    # 과정관리 > 훈련일정관리
    path('lfcourse/train/', views.train_list, name='office_train_list'),
    path('lfcourse/train/write/', views.train_write, name='office_train_write'),
    path('lfcourse/train/modify/<int:pk>/', views.train_modify, name='office_train_modify'),
    path('lfcourse/train/del/<int:pk>/', views.train_del, name='office_train_delete'),

    # 과정관리 > 프로모션관리
    path('lfcourse/promotion/', views.promotion_list, name='office_promotion_list'),
    path('lfcourse/promotion/input/', views.promotion_input, name='office_promotion_input'),
    path('lfcourse/promotion/member-del/', views.promotion_member_del, name='office_promotion_member_delete'),
    path('lfcourse/promotion/member-popup/', views.promotion_member_popup, name='office_promotion_member_popup'),

    # 과정관리 > AJAX
    path('lfcourse/ajax/stadium/', views.ajax_course_stadium, name='office_ajax_course_stadium'),

    # 과정관리 > 팝업
    path('lfcourse/popup/course-list/', views.course_list_popup, name='office_course_list_popup'),

    # ── REPORT ──────────────────────────────────────────
    path('report/weekly/', rpt.report_weekly, name='office_report_weekly'),
    path('report/total-data/', rpt.report_total_data, name='office_report_total_data'),
    path('report/total-data/excel/', rpt.report_total_data_excel, name='office_report_total_data_excel'),
    path('report/total-data-daily/', rpt.report_total_data_daily, name='office_report_total_data_daily'),
    path('report/total-data-daily/excel/', rpt.report_total_data_daily_excel, name='office_report_total_data_daily_excel'),
    path('report/sale-list/', rpt.report_sale_list, name='office_report_sale_list'),
    path('report/sale-list/excel/', rpt.report_sale_list_excel, name='office_report_sale_list_excel'),
    path('report/sale-day-list/', rpt.report_sale_day_list, name='office_report_sale_day_list'),
    path('report/sale-day-list/excel/', rpt.report_sale_day_list_excel, name='office_report_sale_day_list_excel'),
    path('report/now-data/', rpt.report_now_data, name='office_report_now_data'),
    path('report/now-data/excel/', rpt.report_now_data_excel, name='office_report_now_data_excel'),
    path('report/now-statics-1/', rpt.report_now_statics_1, name='office_report_now_statics_1'),
    path('report/now-statics-2/', rpt.report_now_statics_2, name='office_report_now_statics_2'),
    path('report/now-statics-2/load/', rpt.report_now_statics_2_load, name='office_report_now_statics_2_load'),
    path('report/order-list/', rpt.report_order_list, name='office_report_order_list'),
    path('report/order-list/excel/', rpt.report_order_list_excel, name='office_report_order_list_excel'),
    path('report/order-list-dedup/', rpt.report_order_list_dedup, name='office_report_order_list_dedup'),
    path('report/order-list-dedup/excel/', rpt.report_order_list_dedup_excel, name='office_report_order_list_dedup_excel'),
    path('report/new-student/', rpt.report_new_student, name='office_report_new_student'),
    path('report/new-student/excel/', rpt.report_new_student_excel, name='office_report_new_student_excel'),
    path('report/end-student/', rpt.report_end_student, name='office_report_end_student'),
    path('report/end-student/excel/', rpt.report_end_student_excel, name='office_report_end_student_excel'),
    path('report/anal-end/', rpt.report_anal_end, name='office_report_anal_end'),
    path('report/anal-end/excel/', rpt.report_anal_end_excel, name='office_report_anal_end_excel'),
    path('report/delay-data/', rpt.report_delay_data, name='office_report_delay_data'),
    path('report/delay-data/excel/', rpt.report_delay_data_excel, name='office_report_delay_data_excel'),
    path('report/attendance-month/', rpt.report_attendance_month, name='office_report_attendance_month'),
    path('report/attendance-month/excel/', rpt.report_attendance_month_excel, name='office_report_attendance_month_excel'),
    path('report/stadium-year/', rpt.report_stadium_year, name='office_report_stadium_year'),
    path('report/stadium-year/excel/', rpt.report_stadium_year_excel, name='office_report_stadium_year_excel'),
    path('report/coach-miban/', rpt.report_coach_miban, name='office_report_coach_miban'),
    path('report/each-coachdata/', rpt.report_each_coachdata, name='office_report_each_coachdata'),
    path('report/pay-master/', rpt.report_pay_master, name='office_report_pay_master'),
    path('report/raw-data/', rpt.report_raw_data, name='office_report_raw_data'),
    path('report/month-coachdata/', rpt.report_month_coachdata, name='office_report_month_coachdata'),
    path('report/year-coachdata/', rpt.report_year_coachdata, name='office_report_year_coachdata'),
    # REPORT > AJAX
    path('report/ajax/local/', rpt.ajax_report_local, name='office_report_ajax_local'),
    path('report/ajax/stadium/', rpt.ajax_report_stadium, name='office_report_ajax_stadium'),
    path('report/ajax/course/', rpt.ajax_report_course, name='office_report_ajax_course'),

    # ── 포탈관리 ──────────────────────────────────────────
    # 팝업관리
    path('portal/popup/', portal.popup_list, name='office_popup_list'),
    path('portal/popup/write/', portal.popup_write, name='office_popup_write'),
    path('portal/popup/del/', portal.popup_del, name='office_popup_del'),

    # 게시판관리
    path('portal/board/', portal.board_list, name='office_board_list'),
    path('portal/board/content/', portal.board_content, name='office_board_content'),
    path('portal/board/write/', portal.board_write, name='office_board_write'),
    path('portal/board/reply/', portal.board_reply, name='office_board_reply'),
    path('portal/board/del/', portal.board_del, name='office_board_del'),
    path('portal/board/comment/add/', portal.board_comment_add, name='office_board_comment_add'),
    path('portal/board/comment/del/', portal.board_comment_del, name='office_board_comment_del'),
]
