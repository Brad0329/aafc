<!--
// 우편번호
function openZipcode(target) {
	openPopup("/shop/pop_search_zip.asp?target="+target, "Zipcode", 100, 100, "left=200, top=200");
}

function inputZipcode(frzip, rezip, addr, target) {
	var f = document.Frm;
	if (target == "ordPost") {
		f.ordPost.value = frzip+"-"+rezip;
		f.ordAddr.value = addr;
		f.ordAddrDetail.focus();
	}
	else {
		f.rcvPost.value = frzip+"-"+rezip;
		f.rcvAddr.value = addr;
		f.rcvAddrDetail.focus();
	}
}

// 받는분 정보 복사
function copyInfo(item) {
	var f = document.Frm;

	if (item.checked) {
		f.rcvName.value = f.ordName.value;
		f.rcvTel1.value = f.ordTel1.value;
		f.rcvTel2.value = f.ordTel2.value;
		f.rcvTel3.value = f.ordTel3.value;
		f.rcvMobile1.value = f.ordMobile1.value;
		f.rcvMobile2.value = f.ordMobile2.value;
		f.rcvMobile3.value = f.ordMobile3.value;
		f.rcvPost.value = f.ordPost.value;
		f.rcvAddr.value = f.ordAddr.value;
		f.rcvAddrDetail.value = f.ordAddrDetail.value;
		f.rcvEmail.value = f.ordEmail.value;
	}
	else {
		f.rcvName.value = '';
		f.rcvTel1.value = '';
		f.rcvTel2.value = '';
		f.rcvTel3.value = '';
		f.rcvMobile1.value = '';
		f.rcvMobile2.value = '';
		f.rcvMobile3.value = '';
		f.rcvPost.value = '';
		f.rcvAddr.value = '';
		f.rcvAddrDetail.value = '';
		f.rcvEmail.value = '';
	}
}

// 결제금액 계산
function calcSettlePrice() {
	var f = document.Frm;
	var f2 = document.tos_form;
	var totalCouponDiscountPrice, usePoint;

	var orgSettlePrice = parseInt(f.orgSettlePrice.value, 10);
	
	if (f.usePoint) {
		usePoint = (f.usePoint.disabled || checkEmpty(f.usePoint)) ? 0 : parseInt(stripComma(f.usePoint.value), 10);
	}

	var settlePrice = orgSettlePrice - usePoint;

	f.settlePrice.value = settlePrice;
	f2.amount.value = settlePrice;
	//document.getElementById("showSettlePrice").innerHTML = formatComma(settlePrice);
}

// # 적립금 사용 : 시작 ######################################################################
function changeUsePoint(item) {
	var f = document.Frm;

	if (item.checked) {
		f.usePoint.value = f.chkUsePoint.value;
	}else{
		f.usePoint.value=0;
		calcSettlePrice();
		resetUsePoint();
		return false;
	}

	var ownPoint = parseInt(f.ownPoint.value, 10);
	var orgSettlePrice = parseInt(f.orgSettlePrice.value, 10);	
	var settlePrice = orgSettlePrice;
	var pointUseLimit = parseInt(f.pointUseLimit.value, 10);


	var isUsePoint = false;
	var usePoint = (checkEmpty(f.usePoint)) ? 0 : parseInt(stripComma(f.usePoint.value), 10);

	if (usePoint <= 0) {
		msg = "사용할 적립금을 입력해 주세요.";
		item.checked = false;

	}
	else if (usePoint > ownPoint) {
		msg = "보유 하신 적립금보다 많은 금액을 입력하셨습니다.";
		item.checked = false;
		f.chkUsePoint.value = "";
		f.usePoint.value = "T";
	}
	else if (usePoint > settlePrice) {
		msg = "결제금액보다 많이 입력하셨습니다.";
		item.checked = false;
		f.chkUsePoint.value = "";
		f.usePoint.value = "T";
	}
	else if (usePoint < pointUseLimit) {
		msg = "최소 사용 포인트는" + pointUseLimit + "점 이상부터 사용 가능합니다."
		item.checked = false;
		f.chkUsePoint.value = "";
		f.usePoint.value = "T";
	}
	else {
		isUsePoint = true;
	}	

	if (isUsePoint) {
		//document.getElementById("showTotalPoint").innerHTML = "-"+formatComma(usePoint)+"P";
		//document.getElementById("trTotalUsePoint").style.display = "";
	}
	else {
		alert(msg);
		item.value = "";
		resetUsePoint();
	}

	calcSettlePrice();
}

function resetUsePoint() {
	var f = document.Frm;

	//document.getElementById("trTotalUsePoint").style.display = "none";
	//document.getElementById("showTotalPoint").innerHTML = "";
}
// # 적립금 사용 : 끝 ######################################################################

// # 결제수단 확인 : 시작 : jylee ######################################################################
function checkPayway() {
	var f = document.Frm;
	var payway = getRadioVal(f.payway);


	if (typeof f.isCashReceipt != 'undefined') {
		if (payway == CONST_PAYWAY_CARD) {
			setRadioVal(f.isTax, 'F');
			setRadioVal(f.isCashReceipt, 'F');
			setRadioDisabledAll(f.isTax, true);
			setRadioDisabledAll(f.isCashReceipt, true);
		}
		else {
			setRadioDisabledAll(f.isTax, false);
			setRadioDisabledAll(f.isCashReceipt, false);
		}
	}
	if (payway == CONST_PAYWAY_ONLINE) {
		f.onlineDepositor.disabled = false;
	}
	else {
		f.onlineDepositor.disabled = true;
	}
}
// # 결제수단 확인 : 끝 : jylee ######################################################################

// # 주문 : 시작 ######################################################################
var imgPath;
var ingSrc, paySrc;
var payPop;
var payIng = 0;


/* KCP에 사용함*/
function orderChk() {

	var con = confirm("결제 완료 후 완료 페이지로 이동 전까지 새로고침이나 뒤로가기 버튼을 누르지 말아주세요");
	if (!con) {
		return;
	}

	var f = document.Frm;
	var errMsg, errCnt;
	var msg;

	paySrc = "/images/shop/btn04.gif";
	ingSrc = "/images/shop/btn06.gif";

	if (payIng == 1) {
		alert("결제가 진행중입니다. 잠시만 기다려주세요. 확인버튼을 눌러주세요.");
		return;
	}

	errMsg = "입력하지 않은 정보가 있습니다.\n--------------------------------------------------------\n";
	errCnt = 0;
	
	if(getRadioVal(f.sel_child)==""){
		alert("자녀를 선택하세요.");
		return;
	} else {
		f.sel_child.value = getRadioVal(f.sel_child);
	}		
	 //alert("자녀아이디 =" + f.sel_child.value);
	
	if (checkEmpty(f.ordName)) {																								errMsg += "이름\n"; ++errCnt;}
	if (checkEmpty(f.ordTel1) || checkEmpty(f.ordTel2) || checkEmpty(f.ordTel3)) {					errMsg += "전화번호\n"; ++errCnt;}
	if (checkEmpty(f.ordPost)) {																									errMsg += "우편번호\n"; ++errCnt;}
	if (checkEmpty(f.ordAddr) || checkEmpty(f.ordAddrDetail)) {												errMsg += "주소\n"; ++errCnt;}

	if (checkEmpty(f.rcvName)) {																								errMsg += "이름(받는분)\n"; ++errCnt;}
	if (checkEmpty(f.rcvTel1) || checkEmpty(f.rcvTel2) || checkEmpty(f.rcvTel3)) {						errMsg += "전화번호(받는분)\n"; ++errCnt;}
	if (checkEmpty(f.rcvPost)) {																									errMsg += "우편번호(받는분)\n"; ++errCnt;}
	if (checkEmpty(f.rcvAddr) || checkEmpty(f.rcvAddrDetail)) {													errMsg += "주소(받는분)\n"; ++errCnt;}

	//if (getRadioVal(f.payway) == "ONLINE" && checkEmpty(f.onlineDepositor)) {						errMsg += "입금자명\n"; ++errCnt;}

	if (errCnt > 0) {
		alert(errMsg);
		return;
	}

	errMsg = "정확하지 않은 정보가 있습니다.\n--------------------------------------------------------\n";
	errCnt = 0;

	if (!checkEmpty(f.ordEmail)) {
		if (!checkEmail(f.ordEmail.value)) {			errMsg += "형식에 맞지 않는 이메일 주소입니다.\n"; ++errCnt;}
	}
	if (f.ordAddr.value.length < 5) {					errMsg += "주소를 자세히 기입하세요.\n"; ++errCnt;}
//	if (checkSpecialChar(f.ordAddr.value)) {		errMsg += "주소에 특수문자를 사용할 수 없습니다.\n"; ++errCnt;}

	if (errCnt > 0) {
		alert(errMsg);
		return;
	}

	var orgSettlePrice = parseInt(f.orgSettlePrice.value, 10);
	var settlePrice = parseInt(f.settlePrice.value, 10);	
	
	//alert("orgSettlePrice : " + orgSettlePrice);
	//alert("settlePrice : " + settlePrice);

	//var payway = getRadioVal(f.payway);
	var payway = $(":input:radio[name=payway]:checked").val();

	// 온라인입금 (10만원 이상 에스크로 적용)
	if (payway == CONST_PAYWAY_ONLINE) {
		/* 에스크로 결제
		if (f.isEscrow.value == "T" && settlePrice >= 100000) {
			if (confirm("10만원이상 결제하실 경우 에스크로를 이용하실 수 있습니다.\n에스크로를 이용하여 결제를 진행하시겠습니까?")) {
				payVirtual(f, true);
				return;
			}
		}*/

		document.getElementById("btnSettle").src = ingSrc;
		payIng = 2;

		f.action = "/shop/order_process.asp";
		f.target = "_self";
		f.submit();
		return;

	} else { // 신용카드, 실시간계좌이체, 가상계좌
		
		if (settlePrice < 1000) {
			var strPayway;
			switch (payway) {
				case CONST_PAYWAY_CARD :		strPayway = "신용카드"; break;
				case CONST_PAYWAY_BANK :		strPayway = "계좌이체"; break;
				case CONST_PAYWAY_VIRTUAL :		strPayway = "가상계좌"; break;
				case CONST_PAYWAY_ZERO :		strPayway = "제로페이"; break;
			}
			alert("1000원 미만의 금액은 "+strPayway+"를 이용하여 결제하실 수 없습니다.");
			return;
		}

		if (payway == CONST_PAYWAY_CARD) {
			payCard(f);
		}
		else {
			var isEscrow = false;

			/*/ 에스크로 결제
			if (f.isEscrow.value == "T" && settlePrice >= 100000) {
				if (confirm("10만원이상 결제하실 경우 에스크로를 이용하실 수 있습니다.\n에스크로를 이용하여 결제를 진행하시겠습니까?")) {
					isEscrow = true;
				}
			}*/

			switch (payway) {
				case CONST_PAYWAY_BANK :			payBank(f, isEscrow); break;
				case CONST_PAYWAY_VIRTUAL :		payVirtual(f, isEscrow); break;
				case CONST_PAYWAY_ZERO :		payVirtual(f, isEscrow); break;
			}
		}

		return;
	}
}

/*
function openPayProgress() {
	var f = document.Frm;
	payPop = openPopup(f.payPath.value+"/progress/pop_pay.html", "PayProgress", 300, 160);
}
*/
function clearVerifyPay() {
	document.getElementById("verifyPay").src = "";
}

function payCard(f) {
	//setPgInfo(f);
	//f.pay_method.value = "100000000000";
	checkPay(f);
}

function payBank(f, isEscrow) {
	//setPgInfo(f);
	//f.pay_method.value = "010000000000";
	//f.escw_used.value = (isEscrow) ? "Y" : "";
	//f.pay_mod.value = (isEscrow) ? "Y" : "O";

	checkPay(f);
}

function payVirtual(f, isEscrow) {
	//setPgInfo(f);
	//f.pay_method.value = "010000000000";
	//f.escw_used.value = (isEscrow) ? "Y" : "";
	//f.pay_mod.value = (isEscrow) ? "Y" : "O";

	checkPay(f);
}


function checkPay(f) {

	/*
	f.action = "/_engine/shop/shop_makeorder.asp";
	f.submit();
	*/

	if (Frm.chkUsePoint.value != "") {
		if (Frm.isUsePoint.checked == false) {
			alert("적립포인트 사용이 체크되어있지 않습니다. 확인하여 주세요");
			return;
		}
	}

	var settlePrice = Frm.settlePrice.value;
	payForm.good_mny.value = settlePrice;
	pay_form.good_mny.value = settlePrice;
	order_info.good_mny.value = settlePrice;

	var payDevice = $("#payDevice").val();

	//데이타 검증이 끝나면 결제를 위해 주문 데이타 생성한다. 
	var data = $("#Frm").serialize();
	$.post("/_engine/shop/shop_makeorder.asp", data )
		.done(function(data) {
			if(data == "NL") {
				alert("로그인 정보가 없습니다. -새로고침 후 로그인 페이지로 이동하여 주세요-");
				return;
			} else if (data == "NP") {
				alert("부모님 ID만 구매 가능합니다.");
				return;
			} else if (data == "NO_PR") {
				alert("결제금액이 0입니다.");
				return;
			} else if (data == "E101") {
				alert("주문시도 데이타가 없습니다.");
				return;
			} else if (data == "E102") {
				alert("보유 하신 적립금보다 많은 금액을 사용하셨습니다.\n\n확인 후 다시 주문해주세요");
				return;
			} else if (data == "E104") {
				alert("최종 결제금액이 정확하지 않습니다. 다시 주문해주세요.");
				return;
			} else if (data == "E1100") {
				alert("판매중이 아니거나 품절된 상품이 존재합니다. 다시한번 확인해주세요.");
				return;
			} else if (data == "E1101") {
				alert("재고량이 부족한 상품이 존재합니다.(1)\n\n확인 후 다시 주문해주세요.");
				return;
			} else if (data == "E1102") {
				alert("재고량이 부족한 상품이 존재합니다.(2)\n\n확인 후 다시 주문해주세요.");
				return;
			} else {
				//주문데이타가 생성되었으면 실제 결제페이지로 이동
				Frm.chkUsePoint.readOnly = true;
				
				
				var payway = $(":input:radio[name=payway]:checked").val();

				if (payway == "ZEROPAY") {
					payForm.param_opt_1.value = data;
					virtual_pay();

				} else {

					if (payDevice == "PC") {
						payForm.param_opt_1.value = data;
						if ($('input[name="payway"]:checked').val() == "CARD") {
							payForm.pay_method.value = "100000000000";
						} else {
							payForm.pay_method.value = "010000000000";
						}
						//ShowMask();
						pc_pay();
					} else {
						payForm.param_opt_1.value = data;
						if ($('input[name="payway"]:checked').val() == "CARD") {
							order_info.ActionResult.value = "card";
							order_info.pay_method.value = "CARD";
						} else {
							order_info.ActionResult.value = "acnt";
							order_info.pay_method.value = "BANK";
						}
						mobile_pay();
					}
				}
				
			}

		});



}




//-->