/* 원복 스크립트 주석처리
function receiptView(tno){
	
	
	receiptWin = "http://admin.kcp.co.kr/Modules/Sale/Card/ADSA_CARD_BILL_Receipt.jsp?c_trade_no=" + tno;
	window.open(receiptWin , "" , "width=440, height=810");
}
*/
function receiptView(tno,rs_pay_method){
	var pay = rs_pay_method;
	if(pay == "CARD") {
	  receiptWin = "http://admin.kcp.co.kr/Modules/Sale/Card/ADSA_CARD_BILL_Receipt.jsp?c_trade_no=" + tno;
	}else if(pay == "VACCT") {
		receiptWin = "https://admin8.kcp.co.kr/assist/bill.BillAction.do?cmd=vcnt_bill&tno=" + tno;
	}else{
		alert("카드와 가상계좌 이외 건은 조회가 불가능합니다");
		return true;
	}
	alert("호출url = " + receiptWin);
	window.open(receiptWin , "" , "width=440, height=810");
}


  // 현금영수증 연동 스크립트
  function receiptView2( site_cd, order_id, bill_yn, auth_no ) {
    receiptWin2 = "https://admin.kcp.co.kr/Modules/Service/Cash/Cash_Bill_Common_View.jsp";
    receiptWin2 += "?";
    receiptWin2 += "term_id=PGNW" + site_cd + "&";
    receiptWin2 += "orderid=" + order_id + "&";
    receiptWin2 += "bill_yn=" + bill_yn + "&";
    receiptWin2 += "authno=" + auth_no ;
 
    window.open(receiptWin2 , "" , "width=360, height=645, scrollbars=yes, status=no, toolbar=no, resizable=no, location=no, menu=no, ");
  }



// 원본이미지 보기 ##################################################
function openOrgImageView(path) {
	if (path.stripspace() == "") return;
	openPopup("/shopping/pop_orgImageView.asp?path="+encodeURI(path), "OrgImageView", 100, 100, "status=yes, resizable=yes");
}

	//널체크
    function chec_fun (w_obj, al_txt) {		
        if (w_obj.value.split().join("") == "" ) {
            alert(al_txt + "을(를) 입력하세요" );
            w_obj.focus();
            return false;
        } else {
            return true;
        }
    }
    
    //숫자체크
    function chec_num (w_obj, al_txt) {
        if (w_obj.value.split().join("") == "" ) {
            return true;
        } else {
    		if (isNaN(w_obj.value)) {
                alert(al_txt + "은(는) 숫자만 입력 가능합니다." );
    			w_obj.value = "";
    			w_obj.focus();
    			return false;
    		}                
        }
    }

    function setSelect(srcSel, tarSel, sub_con){
        var srcLength = eval(srcSel).length -1;
        delselect(tarSel);
        
        eval(tarSel).options[0] = new Option();
        eval(tarSel).options[0].value = "";
        eval(tarSel).options[0].title = "";
        eval(tarSel).options[0].text =  "==선택==";
        j = 1;
        for (var i=0 ; i <= srcLength ; i++) {
            if ( eval(srcSel).options[i].title == trim(sub_con)) {
                eval(tarSel).options[j] = new Option();
                eval(tarSel).options[j].value = eval(srcSel).options[i].value;
                eval(tarSel).options[j].title = eval(srcSel).options[i].title;
                eval(tarSel).options[j].text =  eval(srcSel).options[i].text;
                j++;
            }
        }
    }        

    //셀렉트 박스 지우기
    function delselect(tarSel) {
        for ( var i=eval(tarSel).length-1 ; i >=0  ; i--) {
            eval(tarSel).options[i] = null;                
        }
    }

    function trim(s_Word) {   
    	var i_Len = s_Word.length;
    	var i_StrLen = 0;
    	while ((i_StrLen < i_Len) && (s_Word.charAt(i_StrLen) <= " "))
    	    i_StrLen++;
    	while ((i_StrLen < i_Len) && (s_Word.charAt(i_Len - 1) <= " "))
    	    i_Len--;
    	return ((i_StrLen > 0) || (i_Len < s_Word.length)) ? s_Word.substring(i_StrLen, i_Len) : s_Word;
    
    }    
    
    function MM_openBrWindow(theURL,winName,features) { //v2.0
        window.open(theURL,winName,features);
    }



if (navigator.userAgent.toLowerCase().indexOf("msie") != -1) {
	try { document.execCommand('BackgroundImageCache', false, true); } catch(e) {}
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

// 이벤트 추가 ##################################################
function addEvent(obj, type, listener) {
	if (window.addEventListener) obj.addEventListener(type, listener, false);
	else obj.attachEvent('on'+type, listener);
}

// 이벤트 추가 ##################################################
function removeEvent(obj, type, listener) {
	if (window.removeEventListener) obj.removeEventListener(type, listener, false);
	else obj.detachEvent('on'+type, listener);
}

// 팝업 ##################################################
function openPopup(theURL, winName, width, height, remFeatures) {
	var features = "";
	if (typeof winName == "undefined") winName = "";
	if (typeof width != "undefined") features += ((features) ? "," : "")+"width="+width;
	if (typeof height != "undefined") features += ((features) ? "," : "")+"height="+height;
	if (typeof remFeatures != "undefined") features += ((features) ? "," : "")+remFeatures;
	if (features.indexOf("status") < 0) features += ",status=yes";

	var popup = window.open(theURL, winName, features);
	popup.focus();

	return popup;
}

// 팝업 - 팝업창 화면중앙 오픈 ##################################################
function openPopupCenter(theURL, winName, width, height, remFeatures) {
	var left = (screen.width/2) - (width/2);
	var top = (screen.availHeight/2) - (height/2);
	var features = "left="+left+",top="+top+",width="+width+",height="+height;
	if (typeof winName == "undefined") winName = "";
	if (typeof remFeatures != "undefined") features += ","+remFeatures;
	if (features.indexOf("status") < 0) features += ",status=yes";

	var popup = window.open(theURL, winName, features);
	popup.focus();

	return popup;
}

// 팝업 - 팝업창 사이즈 조정 ##################################################
function resizePopupWindow(width, height) {
	var userAgent = navigator.userAgent.toLowerCase();
	var isMSIE = (userAgent.indexOf('msie') != -1);
	var agentVer = 0;
	if (isMSIE) {
		var pos_msie = userAgent.indexOf('msie ');
		agentVer = parseInt(userAgent.substring(pos_msie+5, userAgent.indexOf(".", pos_msie)), 10);
	}
	var isMoz = (userAgent.indexOf('gecko') != -1);
	var isChrome = (userAgent.indexOf('chrome') != -1);

	var resizeWidth = width + 10;
	var resizeHeight = height + ((isMSIE && agentVer>6) ? 71 : (isMoz ? (isChrome ? 55 : 81) : 49));

	window.resizeTo(resizeWidth, resizeHeight);

	if (!isChrome) {
		var lastHeight = resizeHeight - (parseInt(document.body.clientHeight, 10) - height);
		if (resizeHeight != lastHeight) { window.resizeTo(resizeWidth, lastHeight); }
	}
}

// 팝업 - 팝업창 자동 사이즈 ##################################################
function autoresizeWindow() {
	var userAgent = navigator.userAgent.toLowerCase();
	var maxX, maxY;
	var thisX, thisY;
	var marginY = 0;
	maxX  = screen.width - 50;
	maxY  = screen.height- 50;
	thisX = document.body.scrollWidth;
	thisY = document.body.scrollHeight;

	if( userAgent.indexOf("msie 6") > 0 ){       marginY = 60; }
	else if( userAgent.indexOf("msie 7") > 0 ){  marginY = 80; }
	else if( userAgent.indexOf("firefox") > 0 ){ marginY = 50; }
	else if( userAgent.indexOf("opera") > 0 ){   marginY = 30; }
	else if( userAgent.indexOf("netscape") > 0 ){marginY = -2; }
	else {                                       marginY = 60; }

	if( thisX > maxX ) thisX = maxX;
	if( thisY > maxY - marginY ){ thisX += 19; thisY = maxY - marginY; }

	window.resizeTo(thisX, thisY);

}

function windowresize(){
    var heightBody= 0;
    var widthBody = 0;
    var heightWin = 0;
    var widthWin  = 0;

    var heightGap = 0;
    var widthGap  = 0;

    heightBody= document.body.scrollHeight;
    widthBody = document.body.scrollWidth;
    heightWin = document.body.clientHeight;
    widthWin  = document.body.clientWidth;
    heightGap = heightWin - heightBody;
    widthGap  = widthWin - widthBody;

    if( heightGap > 0 || heightGap < 0)
        top.window.resizeBy(0,-heightGap);

    if( widthGap > 0 || widthGap < 0)
        window.resizeBy(-widthGap,0);
}

// 팝업 - 팝업창 위치 조정 ##################################################
function movePopupWindow(left, top) {
	window.moveTo(left, top);
}

// 모달 ##################################################
function MM_openModal(theURL, obj, features) {
	window.showModalDialog(theURL, obj, features);
}

// 키 관련 함수 ##################################################
function blockKey(e) {
	var e = window.event || e;
	if (window.event) {
		e.returnValue = false;
	}
	else {
		if (e.which != 8) e.preventDefault(); // 8 : Back Space
	}
}

function blockEnter(e) {
	var e = window.event || e;
	if (window.event) {
		if (e.keyCode == 13) e.returnValue = false;
	}
	else {
		if (e.which == 13) e.preventDefault();
	}
}

function blockNotNumber(e) {
	var e = window.event || e;
	if (window.event) {
		if (e.keyCode < 48 || e.keyCode > 57) e.returnValue = false;
	}
	else {
		if (e.which != 8 && (e.which < 48 || e.which > 57)) e.preventDefault(); // 8 : Back Space
	}
}

function onEnter(e, exec) {
	var e = window.event || e;
	var keyCode = (window.event) ? e.keyCode : e.which;
	if (keyCode == 13) eval(exec);
}

// 즐겨찾기 추가 ##################################################
// 예) <a href="javascript:;" onClick="addFavorites('홈페이지', 'http://www.homepage.com');">즐겨찾기 등록</a>
function addFavorites(title, url) {
	if (document.all) { // IE
		window.external.AddFavorite(url, title);
	}
	else if (window.sidebar) { // Firefox
		window.sidebar.addPanel(title, url, "");
	}
	else { // Opera, Safari ...
		alert("현재 브라우져에서는 이용할 수 없습니다.");
		return;
	}
}

// 시작페이지 설정 ##################################################
// 예) <a href="javascript:;" onClick="setStartPage(this, 'http://www.homepage.com');">시작페이지로</a>
function setStartPage(obj, url) {
	if (document.all && window.external) { // IE
		obj.style.behavior = "url(#default#homepage)";
		obj.setHomePage(url);
	}
	else { // Firefox, Opera, Safari ...
		alert("현재 브라우져에서는 이용할 수 없습니다.");
		return;
    }
}

// 페이지 이동 ##################################################
function gotoUrl(url) {
	if (url.stripspace() != "") {
		location.href = url;
	}
}

// 페이지 최상단으로 ##################################################
function goTop() {
	window.scrollTo(0, 0);
}

// 이미지 미리보기 ##################################################
function previewImage(obj, imgId) {
	var objImg = document.getElementById(imgId);

	if (obj.value.stripspace() == "") return;

	var ext = getFileExt(obj.value).toUpperCase();

	if (ext == 'JPG' || ext == 'GIF' || ext == 'BMP' || ext == 'PNG') objImg.src = obj.value;
}

// 이미지 사이즈 줄이기 ##################################################
function resizeImage(objImg, limitId) {
	if (typeof (objImg) != "object") objImg = document.getElementById(objImg);
	var objParent = objImg.parentNode;
	var imgWidth = parseInt(objImg.width, 10);
	var fixWidth = imgWidth;

	if (typeof limitId == 'undefined') return;

	while (objParent) {
		if (objParent && objParent.id == limitId) {
			fixWidth = objParent.clientWidth;
			break;
		}
		objParent = objParent.offsetParent;
	}

	if (imgWidth > fixWidth) {
		objImg.width = fixWidth;
	}
}

function resizeImageAll(limitId) {
	var objLimit = document.getElementById(limitId);
	if (objLimit) {
		var fixWidth = objLimit.clientWidth;
		var arrImgs = objLimit.getElementsByTagName("IMG");
		for (var i=0, len=arrImgs.length; i<len; i++) {
			if (parseInt(arrImgs[i].width, 10) > fixWidth) {
				arrImgs[i].width = fixWidth;
			}
		}
	}
}

// IFRAME RESIZE 함수 ##################################################
function resizeFrame(iframeWindow, minWidth, minHeight, fixWidth, fixHeight) {
	if (!iframeWindow.name) return false;

	var iframeElement = document.getElementById(iframeWindow.name);
	var resizeWidth = 0;
	var resizeHeight = 0;

	minWidth = (minWidth ? parseInt(minWidth, 10) : 0);
	minHeight = (minHeight ? parseInt(minHeight, 10) : 0);
	fixWidth = (fixWidth ? parseInt(fixWidth, 10) : 0);
	fixHeight = (fixHeight ? parseInt(fixHeight, 10) : 0);

	if (document.all) { // ie
		if (iframeWindow.document.compatMode && iframeWindow.document.compatMode != 'BackCompat') {
			resizeWidth = iframeWindow.document.documentElement.scrollWidth;
			resizeHeight = iframeWindow.document.documentElement.scrollHeight;
		}
		else {
			resizeWidth = iframeWindow.document.body.scrollWidth;
			resizeHeight = iframeWindow.document.body.scrollHeight;
		}
	}
	else {
		resizeWidth = iframeWindow.document.body.scrollWidth;
		resizeHeight = iframeWindow.document.body.scrollHeight;
	}

	if (minWidth > 0 && resizeWidth < minWidth) resizeWidth = minWidth;			// 최소 폭
	if (minHeight > 0 && resizeHeight < minHeight) resizeHeight = minHeight;		// 최소 높이

	if (fixWidth > 0) resizeWidth = fixWidth;		// 고정 폭
	if (fixHeight > 0) resizeHeight = fixHeight;	// 고정 높이

	if (fixWidth > -1) iframeElement.style.width = resizeWidth + 'px';
	if (fixHeight > -1) iframeElement.style.height = resizeHeight + 'px';
}

// 현재 이벤트객체 Index 가져오기 ##################################################
function getDisObjIdx(obj) {
	var i = 0;
	var result = 0;

	var arrTag = document.getElementsByTagName(obj.tagName);

	if (obj.sourceIndex) {
		while (arrTag[i].sourceIndex < obj.sourceIndex) {
			if (arrTag[i].id == obj.id) ++result;
			++i;
		}
	}
	else if (obj.compareDocumentPosition) {
		while ((arrTag[i].compareDocumentPosition(obj) & 6) - 3 > 0) {
			if (arrTag[i].id == obj.id) ++result;
			++i;
		}
	}

	return result;
}

// 체크박스 전체선택 ##################################################
function checkCbAll(cbList, isChecked) {	
	if (cbList) {		
		if (typeof(cbList.length) == "undefined") {
			if (!cbList.disabled) cbList.checked = isChecked;
		}
		else {
			for (var i=0; i<cbList.length; i++) {					
				if (cbList[i].type.toUpperCase() == 'CHECKBOX') {
					if (cbList[i].value.stripspace() != "" && !cbList[i].disabled) {
						cbList[i].checked = isChecked;						
					}
				}
			}
		}
	}
}

// 텍스트 길이 확인 (일반) ##################################################
function checkTextLen(obj, mLen) {
	if (obj.value.length > mLen){
		alert("1~"+mLen+"자까지 입력이 가능합니다.");
		obj.value = obj.value.substring(0, mLen);
		obj.focus();
		return false;
	}

	return true;
}

// 텍스트 길이 확인 (Byte) ##################################################
function checkTextLenByte(obj, mLen) {
	var i, len;
	var byteLen = 0;
	var value = obj.value;

	for (i=0, len=value.length; i<len; i++) {
		++byteLen;

		if ((value.charCodeAt(i) < 0) || (value.charCodeAt(i) > 127)) ++byteLen;

		if (byteLen > mLen) {
			alert("1~"+(mLen / 2)+"자의 한글, 또는 2~"+mLen+"자의 영문, 숫자, 문장기호로 입력이 가능합니다.");
			obj.value = value.substring(0, i);
			obj.focus();
			return false;
		}
	}

	return true;
}

// 객체 Offset 가져오기 ##################################################
function getOffset(obj) {
	var offset = { left : 0, top : 0 };
	var parent = obj.offsetParent;

	offset.left = parseInt(obj.offsetLeft, 10);
	offset.top = parseInt(obj.offsetTop, 10);

	while (parent) {
		if (navigator.userAgent.toLowerCase().indexOf("msie") != -1) {
			offset.left += parseInt(parent.offsetLeft, 10)+(isNaN(parseInt(parent.currentStyle.borderLeftWidth, 10))?0:parseInt(parent.currentStyle.borderLeftWidth, 10));
			offset.top += parseInt(parent.offsetTop, 10)+(isNaN(parseInt(parent.currentStyle.borderTopWidth, 10))?0:parseInt(parent.currentStyle.borderTopWidth, 10));
		}
		else {
			offset.left += parseInt(parent.offsetLeft, 10);
			offset.top += parseInt(parent.offsetTop, 10);
		}
		parent = parent.offsetParent;
	}

	return offset;
}

// 텍스트 Byte 길이 가져오기 ##################################################
function getTextByte(value) {
	var i, len;
	var byteLen = 0;

	for (i=0, len=value.length; i<len; i++) {
		if (escape(value.charAt(i)).length >= 4) {
			byteLen += 2;
		}
		else if (escape(value.charAt(i)) != "%0D") {
			++byteLen;
		}
	}

	return byteLen;
}

// 입력 문자길이 확인후 다음항목으로 포커스 옮기기 ##################################################
function goNextFocus(obj, len, next_item) {
	if (obj.value.stripspace().length == len){
		next_item.focus();
	}
}

// 영문 문자열 확인 ##################################################
function strEngCheck(value){
	var i;

	for(i=0;i<value.length-1;i++){
		// 한글 체크 (한글 ASCII코드 : 12593부터)
		if (value.charCodeAt(i) > 12592) return false;
		// 공백 체크
		if (value.charAt(i) == " ") return false;
	}
	return true;
}

// 파일명 확인 ##################################################
function checkFileName(obj) {
	var result = false;

	if (obj.value.stripspace() != "") {
		var fidx = obj.value.lastIndexOf("\\")+1;
		var filename = obj.value.substr(fidx, obj.value.length);
		result = strEngCheck(filename);
	}

	if (!result) {
		alert("파일명을 반드시 영문 또는 숫자로 해주세요.");
		obj.focus();
		return false;
	}
	return true;
}

// 파일 확장자 ##################################################
function getFileExt(value) {
	if (value != "") {
		var fidx = value.lastIndexOf("\\")+1;
		var filename = value.substr(fidx, value.length);
		var eidx = filename.lastIndexOf(".")+1;

		return filename.substr(eidx, filename.length);
	}
}

// 파일확장자 확인 ##################################################
function checkFileExt(obj, exts, errMsg) {
	var arrExt = exts.toLowerCase().split(",");
	var result = false;

	if (obj.value.stripspace() != "") {
		var ext = getFileExt(obj.value).toLowerCase();

		for (var i=0; i<arrExt.length; i++) {
			if (arrExt[i].trim() == ext) result = true;
		}
	}

	if (!result) {
		alert(errMsg);
		obj.focus();
		return false;
	}
	return true;
}

// 영문/숫자 혼용 확인 ##################################################
function checkEngNum(str) {
	var RegExpE = /[a-zA-Z]/i;
	var RegExpN = /[0-9]/;

	return (RegExpE.test(str) && RegExpN.test(str)) ? true : false;
}

// 특수문자 확인 ##################################################
function checkSpecialChar(value) {
	var specialChar = "`~!@#$%^&*_+=|\\[]{}:;,<.>/?'\"";
	for (var i=0, len=specialChar.length; i<len; i++) {
		if (value.indexOf(specialChar.substr(i, 1)) != -1) return true;
	}
	return false;
}

// 아이디 확인 ##################################################
function checkID(value, min, max) {
	var RegExp = /^[a-zA-Z0-9_]*$/i;
	var returnVal = RegExp.test(value) ? true : false;
	if (typeof(min) != "undefined" && value.length < min) returnVal = false;
	if (typeof(max) != "undefined" && value.length > max) returnVal = false;
	return returnVal;
}

// 비밀번호 확인 ##################################################
function checkPass(value, min, max) {
	var RegExp = /^[a-zA-Z0-9]*$/i;
	var returnVal = RegExp.test(value) ? true : false;
	if (typeof(min) != "undefined" && value.length < min) returnVal = false;
	if (typeof(max) != "undefined" && value.length > max) returnVal = false;
	return returnVal;
}

// 숫자 확인 ##################################################
function checkNum(value, isDec) {
	var RegExp;

	if (!isDec) isDec = false;
	RegExp = (isDec) ? /^-?[\d\.]*$/ : /^-?[\d]*$/;

	return RegExp.test(value)? true : false;
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

// URL 확인 ##################################################
function checkUrl(url) {
	var exp = new RegExp("^(http|https)\:\/\/");
	if (exp.test(url.toLowerCase())) {
		return true;
	}
	else {
		return false;
	}
}

// 공백 확인 ##################################################
function checkEmpty(obj) {
	if (obj.value.stripspace() == "") {
		return true;
	}
	else {
		return false;
	}
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

// Radio 설정하기 ##################################################
function setRadioVal(obj, value) {
	var i;

	if (obj) {
		if (typeof(obj.length) == "undefined") {
			if (obj.value == value) {
				obj.checked = true;
			}
		}
		else {
			for(i=0; i<obj.length; i++) {
				if (obj[i].value == value) {
					obj[i].checked = true;
					break;
				}
			}
		}
	}
}

// Radio Disabled 설정하기 ##################################################
function setRadioDisabled(obj, value, disabled) {
	var i;

	if (obj) {
		if (typeof(obj.length) == "undefined") {
			if (obj.value == value) {
				obj.disabled = disabled;
			}
		}
		else {
			for(i=0; i<obj.length; i++) {
				if (obj[i].value == value) {
					obj[i].disabled = disabled;
					break;
				}
			}
		}
	}
}

// Form Disabled 전체 설정하기 ##################################################
function setRadioDisabledAll(obj, disabled) {
	var i;

	if (obj) {
		if (typeof(obj.length) == "undefined") {
			obj.disabled = disabled;
		}
		else {
			for(i=0; i<obj.length; i++) {
				obj[i].disabled = disabled;
			}
		}
	}
}

// Select 설정값 가져오기 ##################################################
function getSelectVal(obj) {
	var value = "";
	var idx = obj.selectedIndex;

	if (idx >= 0){
		value = obj.options[idx].value;
	}

	return value;
}

// Select Option 추가 ##################################################
function selectAddList(obj, text, value) {
	var newOpt = document.createElement("OPTION");
	newOpt.text = text;
	newOpt.value = value;
	obj.options.add(newOpt);
}

// Select Option 전체삭제 ##################################################
function selectRemoveAll(obj) {
	for (var i=obj.length-1; i>=0; i--) {
		selectRemoveList(obj, i);
	}
}

// Select Option 삭제 ##################################################
function selectRemoveList(obj, i) {
	obj.remove(i);
}

// Hidden 추가 ##################################################
function addHidden(f, name, value) {
	var input = document.createElement('INPUT');
	input.type = 'HIDDEN';
	input.name = name;
	input.value = value;
	f.appendChild(input);
}

// 숫자 문자열에서 문자열 제거 ##################################################
function stripCharFromNum(value, isDec) {
	var i;
	var minus = "-";
	var nums = "1234567890"+((isDec) ? "." : "");
	var result = "";

	for(i=0; i<value.length; i++) {
		numChk = value.charAt(i);
		if (i == 0 && numChk == minus) {
			result += minus;
		}
		else {
			for(j=0; j<nums.length; j++) {
				if(numChk == nums.charAt(j)) {
					result += nums.charAt(j);
					break;
				}
			}
		}
	}
	return result;
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

// 내림 ##################################################
// num: 대상 숫자, pos: 대상 자리수
function setFloor(num, pos) {
	if(!pos) pos = 0;
	return Math.floor(num * Math.pow(10, pos)) / Math.pow(10, pos);
}

// 반올림 ##################################################
// num: 대상 숫자, pos: 대상 자리수
function setRound(num, pos) {
	if(!pos) pos = 0;
	return Math.round(num * Math.pow(10, pos)) / Math.pow(10, pos);
}

// 올림 ##################################################
// num: 대상 숫자, pos: 대상 자리수
function setCeil(num, pos) {
	if(!pos) pos = 0;
	return Math.ceil(num * Math.pow(10, pos)) / Math.pow(10, pos);
}

// 강제 소수점 이하 0채우기 ##################################################
// num: 대상 숫자, pos: 출력을 원하는 소수점자리수
function setRoundZero(num, pos) {
	var strNum = stripComma(num.toString());
	var arrNum = strNum.split(".");

	if (arrNum.length <= 1) {
		num = arrNum[0]+".";
		for (var i=0; i<pos; i++) {
			num += "0";
		}
	}
	else {
		num = setRound(num, pos);
	}
	return num;
}

// 소수점 이하 자리수 확인 ##################################################
// num: 대상 숫자, pos: 희망 소수점 이하자리수
function checkRound(num, len) {
	var strNum = stripComma(num.toString());
	var arrNum = strNum.split(".");

	if (arrNum.length > 1 && arrNum[1].length > len) return false;
	else return true;
}

// 숫자 문자열에서 "0" 시작문자 제거 ##################################################
function removePreZero(str) {
	var i, result;

	if (str == "0") return str;

	for (i = 0; i<str.length; i++) {
		if (str.substr(i,1) != "0") break;
	}

	result = str.substr(i, str.length-i);
	return result;
}

// 통화형태로 변환 ##################################################
function toCurrency(obj) {
	if (obj.disabled) return false;

	var num = obj.value.stripspace();
	if (num == "") return false;

	if (!checkNum(stripComma(num))) {
		//alert ("숫자만 입력해주세요.");
		num = stripCharFromNum(num, false);
		obj.blur(); obj.focus();
	}
	num = stripCharFromNum(stripComma(num), false);
	num = removePreZero(num);
	obj.value = formatComma(num);
}

// 숫자입력 확인 ##################################################
function numberOnly(obj, isDec) {
	if (!isDec) isDec = false;
	if (obj.disabled) return false;

	var num = obj.value.stripspace();
	if (num == "") return false;

	if (!checkNum(num, isDec)) {
		//alert ("숫자만 입력해주세요.");
		num = stripCharFromNum(num, isDec);
		obj.blur(); obj.focus();
	}
	num = stripCharFromNum(stripComma(num), isDec);

	var arrNum = num.split(".");
	if (arrNum.length > 1) {
		obj.value = arrNum[0]+"."+arrNum[1];
	}
	else {
		obj.value = arrNum[0];
	}
}

// 숫자 증감 처리 ##################################################
function controlNum(obj, mode, isminus) {
	var num = obj.value;
	if (!isminus) isminus = 0;

	num = (num.stripspace() == "") ? 0 : num;
	num = (isNaN(num)) ? 0 : parseInt(num, 10);

	if (mode == '+') ++num;
	else --num;

	if (isminus != 1 && num < 0) num = 0;

	obj.value = num;
}
