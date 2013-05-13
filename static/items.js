function fill_in_generator(query) {
    $(".single_clause").remove();
    $.each(query, function(index, clause) {
        var id = create_query_clause_element();
        var polarity = clause[0],
            key = clause[1],
            operator = clause[2],
            value = clause[3];

        console.log(id, polarity, key, operator, value)

        $("#" + id + " select.polarity").val(polarity);
        $("#" + id + " select.operator").val(operator);
        $("#" + id + " input.key").val(key);
        $("#" + id + " input.value").val(value);
    });

    create_query_clause_element();
}

function query_obj_from_html(submit_element) {
    // Generate a LQL query based on the filter html widget.
    // Passed in must be the select button element of the widget.
    var clauses = submit_element.parent().find('.single_clause');
    var query = [];

    clauses.each(function(index, e) {
        var e = $(e);
        var polarity = e.find('select.polarity').val();
        
        var subclauses = [];
        e.find(".subclause").each(function(index, sc) {
            var subclause = $(sc);
            var key = subclause.find('input.key').val();
            var value = subclause.find('input.value').val();
            var operator = subclause.find('select.operator').val();
            subclause.push([key, operator, value]);
        });
        
        query.push([polarity, subclauses]);
    });

    return query;
}

function create_query_clause_element(initial_data) {
    var id = Math.floor(Math.random()*119);
    var html = $(".clause.template").html();
    var clause = $("<div id=\"c" + id + "\" class=\"single_clause\">" + html + "</div>");
    $(".query_clauses").append(clause);

    clause.find("a.add_new_subclause").click(function() {
        // bind the listener for making the green plus button work
        create_subclause(id);
    });

    if(initial_data) {
        clause.find("select.polarity").val(initial_data[0]);
        $.each(initial_data[1], function(index, subclause) {
            create_subclause(id, subclause);
        });
    } else {
        create_subclause(id);
    }
}

function create_subclause(id, initial_data) {
    var html = $(".subclause.template").html();
    var subclause = $("<div class=\"subclause\">" + html + "</div>");
    $("#c" + id + " .subclauses").append(subclause);
    
    subclause.find("a.delete_subclause").click(function() {
        subclause.remove()
    });

    if(initial_data) {
        subclause.find(".key").val(initial_data[0]);
        subclause.find(".operator").val(initial_data[1]);
        subclause.find(".value").val(initial_data[2]);
    }
}

$(function() {
    $(".add_clause_buttons button").click(function() {
        var button = $(this);
        var clause;
        if(button.text() == "Including") {
            clause = ['including', [['', 'exact', '']]];
        } else if(button.text() == "Published Today") {
            var yesterday = new Date (new Date() - 24 * 3600 * 1000).toISOString();
            clause = ['including', [['date_published', 'after', yesterday]]];
        }

        create_query_clause_element(clause);
    });

    $(".add_new_query_clause").click(create_query_clause_element);

    $(".submit_query_button").click(function() {
        var query = query_obj_from_html($(this));
        window.location.href = "/items?query=" + encodeURIComponent(query);
    });

    $(".info-icon").click(function(event) {
        var id = $(this).attr("item-id");
        $("#pane_" + id).show('fast');
        event.stopPropagation(); // so this click event doesn't immediatly trigger the hide function.
    });

    $(document).click(function() {
        $('.hidden_pane').hide('fast');
    });
});