
$(document).ready(function() {
    // Set the status of all the buttons to secondary
    $('.btn').addClass('btn-secondary');
    $('#voctobutton-fs-c').removeClass('btn-secondary')
    $('#voctobutton-fs-c').addClass('btn-primary')


    $('.btn').click(function() {
        //When a button is clicked, remove primary from all and set secondary (ie greyed out or a variant)
        $('.btn').removeClass('btn-primary');
        $('.btn').addClass('btn-secondary');

        // And then make currently clicked button the primary and not the secodnary
        $(this).removeClass('btn-secondary');
        $(this).addClass('btn-primary');
    });
});
