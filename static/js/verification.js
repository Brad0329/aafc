$(function(){

	$.fn.onVerification = function(type,msg){
		var venType = "";
		var data=$(this).val();

		switch(type) {
			case "default" : 
				venType = /""/;
				break;
			case "hangul" : 
				venType = /([^ㄱ-ㅎ|ㅏ-ㅣ|가-힝])/;
				break;
			case "number" : 
				venType = /[^0-9]/;
				break;
			case "number2" : 
				venType = /[^0-9]/;
				break;
			case "english" :
				venType =/[^a-zA-Z]/;
				break;
			case "email" :
				venType = /^[0-9a-zA-Z]([-_.]*?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]*?[0-9a-zA-Z])*.[a-zA-Z]{2,3}$/i;
				break;
			case "word" :
				venType = /[^ㄱ-ㅎ가-힝A-Za-z]/g;
				break;
			case "content" : 
				 if (data == "" || data =="<p>&nbsp;</p>")
				 {
					alert(msg);
					$(this).val('');
					$(this).focus();
					return false;
				 }else{
					return true;
				 }
				break;
			default :
				alert("검증 타입을 확인해주세요");
			    return;
		}
		
		if(type=="email"){

			if(!venType.test(data) ||data == ""){
				alert(msg);
				$(this).val('');
				$(this).focus();
				return false;
			}else{
				return true;
			}
		}else if (type=="number2"){
			if(venType.test(data)){
				alert(msg);
				$(this).val('');
				$(this).focus();
				return false;
			}else{
				return true;
			}
		}else{

			if(venType.test(data) ||data == ""){
				alert(msg);
				$(this).val('');
				$(this).focus();
				return false;
			}else{
				return true;
			}
		}
	}

});

