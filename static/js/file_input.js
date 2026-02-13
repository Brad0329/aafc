$( document ).ready(function() {
	$('.file_input input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input input[type=text]').val(fileName);
	});
	$('.file_input1 input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input1 input[type=text]').val(fileName);
	});
	$('.file_input2 input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input2 input[type=text]').val(fileName);
	});
	$('.file_input3 input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input3 input[type=text]').val(fileName);
	});
	$('.file_input4 input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input4 input[type=text]').val(fileName);
	});
	$('.file_input5 input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input5 input[type=text]').val(fileName);
	});
	$('.file_input_multi input[type=file]').change(function() {
		var fileName = $(this).val();
		var fileCount = $(this).get(0).files.length;

		$('.file_input_multi input[type=text]').val(fileCount+"개의 파일이 선택되었습니다.");
	});
});