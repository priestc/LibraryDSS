$(function() {
    $('form.engine_details').submit(function(event) {
        alert("SSS");
        return false;

        var engine_id = $(this).attr('engine-id');
        var form = $("#engine_" + engine_id);

        $.ajax(); // make ajax call then return the result to
        
        $("#result_engine_" + engine_id).text("Saved");
        return false;
    });
});