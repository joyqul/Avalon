$(document).ready(function(){
	$(window).resize(function(){
		var w = $(window).innerWidth();
		if (w > 768) {
            $("nav").show();
		}
        else {
            $("nav").hide();
        }
	});
    $(".menu").click(function() {
		$("nav").toggle();
	});
    $(".history").click(function() {
		$("table").toggle();
	});
});
