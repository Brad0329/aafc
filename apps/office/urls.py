from django.urls import path
from . import views

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
]
