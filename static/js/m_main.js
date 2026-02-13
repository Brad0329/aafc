$(function(){
	function SetupFunction() {
		var s_height = $(window).height();
		$("#m_gnb").css('height',s_height);
	}	

	$(document).ready(SetupFunction);
	$(window).resize(SetupFunction);

	$("#m_gnb").css('overflow-y','auto');
	$("body").css('top','0');
	$("body").css('width','100%');

		
	$(".m_menu").click(function(){
		$("#m_gnb").show('normal');
		$(".m_close").css('display','block');
		$(".m_menu").css('display','none');
		$("body").css('position','fixed');
	});

	$(".m_close").click(function(){
		$("#m_gnb").hide('fast');
		$(".m_close").css('display','none');
		$(".m_menu").css('display','block');
		$("body").css('position','');
	});

	$(document).click(function(e){
		if (!$(e.target).is('.m_menu img') && !$(e.target).is('#m_gnb li') && !$(e.target).is('#m_gnb li a')){
			$('#m_gnb').hide('fast');
			$(".m_close").css('display','none');
			$(".m_menu").css('display','block');
			$("body").css('position','');
		}
	});
	
	$("#m_gnb li").click(function(){
		var submenu = $(this).find("ul");

		if( submenu.is(":visible") ){
			submenu.slideUp();
		}else{
			submenu.slideDown();
		}
	});
});