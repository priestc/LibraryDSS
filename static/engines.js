function show_submit_button() {
    // When the user changes any input element in the engines list,
    // make the corresponding submit box visible.
    var t = $(this);
    var form = t.parents()[0];
    var id = $(form).attr("engine-id");
    $(".submit_engine_changes[engine-id=" + id + "]").css('visibility', 'visible');
}


$(function() {
    $('form.engine_details').submit(function(event) {
        var engine_id = $(this).attr('engine-id');
        var form = $(this);

        $.ajax({
            'url': "/update_engine_details",
        }).complete(function() {
            console.log("ajax completed");
        });
        
        $("#result_engine_" + engine_id).text("Saved");
        return false;
    });

    $('form.engine_details input').keyup(show_submit_button).change(show_submit_button);
});