$(function(){
    $('.notification-close').on('click', function() {
        $(this).parent().remove();
    });
});