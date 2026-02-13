$(document).ready(function(){
	/* 메인 배너 슬라이드 */
	$(".flexslider").flexslider({
		animation: "slide",
		slideshow: true,
		slideshowSpeed:3000,
		animationSpeed:1000
	});

	var delay=300, setTimeoutConst;
	$(".gnb_li").hover(function() {
		var target = $(this);
		$("#header_gnb").css("background","white");
		$("#header_gnb .header_gnb .gnb .gnb_li a").css("color","#1c3d54");
		$("#header_gnb .header_gnb .gnb .gnb_li .gnb_menu li a").css("color","");
		setTimeoutConst = setTimeout(function(){
			$(target).children(".gnb_menu").slideDown("500").show();
		}, delay);
	}, function(){
		$("#header_gnb").css("background","#84b2e0");
		$("#header_gnb .header_gnb .gnb .gnb_li a").css("color","white");
		$("#header_gnb .header_gnb .gnb .gnb_li .gnb_menu li a").css("color","");
		clearTimeout(setTimeoutConst);
		$(".gnb_li").find(".gnb_menu").slideUp("500");
	});
});


// 공백 확인 ##################################################
function checkEmpty(obj) {
	if (obj.value.stripspace() == "") {
		return true;
	}
	else {
		return false;
	}
}



// Trim 함수 ##################################################
// Ex) str = "    테 스트   ".trim(); => str = "테 스트";
String.prototype.trim = function() {
	return this.replace(/(^[ \t\n\r]*)|([ \t\n\r]*$)/g,'');
}

// 문자열 공백제거 함수 ##################################################
// Ex) str = "    테 스   트   ".stripspace(); => str = "테스트";
String.prototype.stripspace = function() {
	return this.replace(/ /g, '');
}

// 전체 문자열 바꾸기 함수 ##################################################
// Ex) str = "a테스트bcd테스트efg".replaceAll("테스트", ""); => str = "abcdefg";
String.prototype.replaceAll = function(a, b) {
	var s = this;
	if (navigator.userAgent.toLowerCase().indexOf("msie") != -1)
		return s.replace(new RegExp(a, 'gi'), b);
	else
		return s.split(a).join(b);
}

// Radio(CheckBox) 설정값 가져오기 ##################################################
function getRadioVal(obj) {
	var i, value = "";

	if (obj) {
		if (typeof(obj.length) == "undefined") {
			if (obj.checked) {
				value = obj.value;
			}
		}
		else {
			for (i=0; i<obj.length; i++) {
				if (obj[i].checked) {
					value = obj[i].value;
					break;
				}
			}
		}
	}
	return value;
}

// 이메일 확인 ##################################################
function checkEmail(email) {
	if (email.search(/^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z0-9]+$/) != -1) {
		return true;
	}
	else {
		return false;
	}
}

// 콤마(,) 제거 ##################################################
function stripComma(str) {
    var re = /,/g;
    return str.replace(re, "");
}

// 숫자 3자리수마다 콤마(,) 찍기 ##################################################
function formatComma(num, pos) {
	if (!pos) pos = 0;  //소숫점 이하 자리수
	var re = /(-?\d+)(\d{3}[,.])/;

	var strNum = stripComma(num.toString());
	var arrNum = strNum.split(".");

	arrNum[0] += ".";

    while (re.test(arrNum[0])) {
        arrNum[0] = arrNum[0].replace(re, "$1,$2");
    }

	if (arrNum.length > 1) {
		if (arrNum[1].length > pos) {
			arrNum[1] = arrNum[1].substr(0, pos);
		}
		return arrNum.join("");
	}
	else {
		return arrNum[0].split(".")[0];
	}
}