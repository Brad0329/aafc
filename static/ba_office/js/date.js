// 날자 유효성 확인 ##################################################
function isDate(strDate){
	var tmpArr;
	var tmpYear, tmpMon, tmpDay;

	if (strDate.length != 10) return false;

	tmpArr = strDate.split("-");

	if (tmpArr.length != 3 ) return false;

	tmpYear = tmpArr[0];
	tmpMon = tmpArr[1];
	tmpDay = tmpArr[2];

	var tDateString = tmpYear+'/'+tmpMon+'/'+tmpDay+' 8:0:0';
	var tmpDate = new Date(tDateString);

	if (isNaN(tmpDate)) return false;

	if (((tmpDate.getFullYear()).toString() == tmpYear) && (tmpDate.getMonth() == parseInt(tmpMon, 10)-1) && (tmpDate.getDate() == parseInt(tmpDay, 10))) {
		return true;
	}
	else {
		return false;
	}
}

// # 날짜 기간 계산 ##################################################
var inputDateConfig = function() {
	this.sdate = null;
	this.edate = null;
	this.type = null;
	this.term = null;
}
var cfgInputDate = new inputDateConfig();

function inputDate(sdate, edate, type, term) {
	cfgInputDate.sdate = (sdate.nodeType==1) ? sdate : document.getElementById(sdate);
	cfgInputDate.edate = edate ? ((edate.nodeType==1) ? edate : document.getElementById(edate)) : null;
	cfgInputDate.type = type;
	cfgInputDate.term = term;

	if (type == 'W') {
		if (cfgInputDate.sdate) cfgInputDate.sdate.value = '';
		if (cfgInputDate.edate) cfgInputDate.edate.value = '';
	}
	else {
		dtAjax.execute("/common/ajax/exec_getDate.asp", "", execInputDate);
	}
}

function execInputDate(req) {
	var value = req.responseText;
	var today;

	if (value.replace(/ /g, "") == "") {
		today = new Date();
	}
	else {
		var arrDate = value.split('-');
		today = new Date(arrDate[1]+'/'+arrDate[2]+'/'+arrDate[0]);
	}
	var now_year = today.getFullYear();
	var now_month = today.getMonth()+1;
	var now_day = today.getDate();

	var sdate = cfgInputDate.sdate;
	var edate = cfgInputDate.edate;
	var type = cfgInputDate.type;
	var term = cfgInputDate.term;

	if (isNaN(term)) term = 0;

	var month_temp = now_month - 1;
	var day_temp = getLastDay(now_year, month_temp);

	var the_day = now_day;
	var the_month = now_month;
	var the_year = now_year;

	if (type == 'T') {
		var opt_day = now_day - term;
		if (opt_day > 0) {
			the_day = opt_day;
		}
		else {
			var opt_month = now_month - 1;
			the_day = day_temp + opt_day;
			if (opt_month > 0) {
				the_month = opt_month;
			}
			else {
				the_year = now_year - 1;
				the_month = 12;
			}
		}
	}
	else if (type == 'D') {
		var opt_day = now_day - term;
		if (opt_day > 0) {
			the_day = opt_day;
		}
		else {
			var opt_month = now_month - 1;
			the_day = day_temp + opt_day;
			if (opt_month > 0) {
				the_month = opt_month;
			}
			else {
				the_year = now_year - 1;
				the_month = 12;
			}
		}
	}
	else if (type == 'M') {
		var opt_month = now_month - term;
		if (opt_month > 0) {
			the_month = opt_month;
		}
		else {
			the_year = now_year - 1;
			the_month = 12 + opt_month;
		}
	}
	else if (type=='Y') {
		the_year = now_year-term;
	}

	var the_ymLastDay = getLastDay(the_year, the_month);
	if (the_ymLastDay < the_day) the_day = the_ymLastDay;

	if (the_month < 10) the_month = '0' + the_month;
	if (the_day < 10) the_day = '0' + the_day;

	var the_date = the_year+'-'+the_month+'-'+the_day;
	sdate.value = the_date;

	if (now_month<10) now_month = '0'+now_month;
	if (now_day<10) now_day = '0'+now_day;

	if (type == 'T' && term > 0) {
		if (edate) edate.value = the_date;
	}
	else {
		now_date = now_year+'-'+now_month+'-'+now_day;
		if (edate) edate.value = now_date;
	}
}

// # 월별 일자수 추출 ##################################################
function getLastDay(year, mon) {
	var last_day = 31;

	switch(mon) {
		case(1): last_day=31; break;
		case(2):
			// 윤년 확인
			if(((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0)) {
				last_day=29;
			}
			else{
				last_day=28;
			}
			break;
		case(3): last_day=31; break;
		case(4): last_day=30; break;
		case(5): last_day=31; break;
		case(6): last_day=30; break;
		case(7): last_day=31; break;
		case(8): last_day=31; break;
		case(9): last_day=30; break;
		case(10): last_day=31; break;
		case(11): last_day=30; break;
		case(12): last_day=31; break;
		default: last_day=31; break;
	}

	return last_day;
}


/* AJAX Request */
var dtAjax = new Object();
dtAjax.xmlHttpReq = null;

dtAjax.execute = function(url, params, returnExec) {
	dtAjax.xmlHttpReq = dtGetXmlHttpRequest();
	if (dtAjax.xmlHttpReq) {
		url += ((url.indexOf('?') >= 0) ? '&' : '?') + "rnd="+Math.random();

		dtAjax.xmlHttpReq.onreadystatechange = function() {
			if (dtAjax.xmlHttpReq.readyState == 4) {
				returnExec(dtAjax.xmlHttpReq);
				dtAjax.xmlHttpReq = null;
			}
		}

		dtAjax.xmlHttpReq.open('GET', url, true);
		dtAjax.xmlHttpReq.send(params);
	}
}

function dtGetXmlHttpRequest() {
	if (window.XMLHttpRequest) {
		// Create XMLHttpRequest object in non-Microsoft browsers
		return new XMLHttpRequest();
	} else if (window.ActiveXObject) {
		// Create XMLHttpRequest via MS ActiveX
		try {
			// Try to create XMLHttpRequest in later versions
			// of Internet Explorer
			return new ActiveXObject("Msxml2.XMLHTTP");
		} catch (e1) {
			// Failed to create required ActiveXObject
			try {
				// Try version supported by older versions
				// of Internet Explorer
				return new ActiveXObject("Microsoft.XMLHTTP");
			} catch (e2) {
				// Unable to create an XMLHttpRequest with ActiveX
			}
		}
	}
	else {
		return null;
	}
}
