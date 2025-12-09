$(function() {
    var csrftoken = $('meta[name="csrf-token"]').attr('content');

    $('#show-header').on('click', function() {
        $('#header').show();
        saveVisibility(true);
        $('#show-header').hide();
        setTimeout(() => {
            location.reload(); 
        }, 5);
    });
    $('#hide-header').on('click', function() {
        $('#header').hide();
        saveVisibility(false);
        $('#show-header').show();
        setTimeout(() => {
            location.reload(); 
        }, 5);
    });



    function saveVisibility(isVisible) {
        $.ajax({
            url: '/set_visibility/',
            type: 'POST',
            data: {
                visible: isVisible,
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                // console.log('保存成功:', response);
            },
            error: function(xhr, status, error) {
                // console.log('エラーが発生しました:', xhr.status, error);
            }
        });
    }
    $.get('/get_visibility/', function(response) {
        if (response.visible) {
            $('#targetElement').show();
        } else {
            $('#targetElement').hide();
        }
    });
});