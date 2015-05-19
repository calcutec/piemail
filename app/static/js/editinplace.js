$( document ).ready(function() {
    var hideToolbar = function() {
        $('.wysihtml5-toolbar').hide();
        $('div[contenteditable="true"]').attr('contenteditable', false);
        $('#edit-button').html("Edit Poem");
    };

    var showToolbar = function() {
        $('.wysihtml5-toolbar:last').show("slow");
        $('div[contenteditable="false"]').attr('contenteditable', true);
        $('#edit-button').html("Submit Changes");
    };

    var editable = false;
    $( "#edit-button" ).click(function() {
        if (!editable){
            showToolbar();
            editable = true;
        } else {
            var header = $('.editme:first').html();
            var content = $('.editme:last').html();
            var post_id = $('#post_id').html();
            hideToolbar();
            editable = false;
            $.ajax({
                type: "POST",
                url:'/edit_in_place',
                data: {header:header, content: content, post_id: post_id}
                //success: function(response)
                //    console.log(response);
                //    $('#editme').html(response);
            });
        }
    });




    $('.editme_full').wysihtml5({
        toolbar: {
            fa: true,
            "style": true,
            "font-styles": true,
            "emphasis": true,
            "lists": true,
            "html": true,
            "link": true,
            "image": true,
            "color": false,
            parser: function(html) {return html;}
        },
        "events": {"load": function() {hideToolbar();}}
    });

    $('#post').wysihtml5({
        toolbar: {
            fa: true,
            "link": false,
            "image": false
        }

    });

    $('#op-ed-post').wysihtml5({
        toolbar: {
            "style": true,
            "font-styles": true,
            "emphasis": true,
            "lists": false,
            "html": true,
            "link": true,
            "image": true,
            "color": true,
            fa: true,
            parser: function(html) {
                return html;
            }
        }

    });
});