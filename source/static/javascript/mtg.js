$(function(){
    const mtgContainerWidth = $('.mtg-container').width();
    $('.group-container').css('max-width', mtgContainerWidth + 'px');
    $(".mtg").on("click", function(event) {
        event.preventDefault();
        const url = $(this).data("join-url");
        if (url) {
            window.open(url, "_blank");
        }
    });
    $(".cancel-join-btn").on("click", function(event) {
        event.preventDefault();
        window.close();
        window.open('', '_self').close();
    });
    $('.mtg-edit').on('click', function(event) {
        event.stopPropagation();
        window.location.href = $(this).data('edit-url');
    });
    $('.mtg-delete').on('click', function(event) {
        event.stopPropagation();
        window.location.href = $(this).data('delete-url');
    });
});