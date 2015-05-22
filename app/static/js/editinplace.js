$( document ).ready(function() {
    var showToolbar = function() {
        if($("body").attr("class") != "wysihtml5-supported") {
            if ($('#user-type').html() == 1) {
                $('#edit-me').wysihtml5({
                    toolbar: {
                        "style": true,
                        "font-styles": true,
                        "emphasis": false,
                        "lists": true,
                        "html": false,
                        "link": true,
                        "image": false,
                        "color": false,
                        fa: true
                    }
                });
            } else {
               $('#edit-me').wysihtml5({
                    toolbar: {
                        "style": true,
                        "font-styles": true,
                        "emphasis": true,
                        "lists": true,
                        "html": false,
                        "link": false,
                        "image": false,
                        "color": false,
                        "quote": false,
                        fa: true
                    }
                });
            }
        } else {
            $('.wysihtml5-toolbar').show()
        }
        $('#edit-button').html("Submit Changes");
    };


    var hideToolbar = function() {
        $('#edit-button').html("Edit Poem");
        $('.wysihtml5-toolbar').hide()
    };

    var editable = false;
    $( "#edit-button" ).click(function() {
        if (!editable){
            showToolbar();
            editable = true;
        } else {
            var content = $('#edit-me').html();
            var post_id = $('#post-id').html();
            hideToolbar();
            editable = false;
            $.ajax({
                type: "POST",
                url:'/edit_in_place',
                data: {content: content, post_id: post_id}
            });
        }
    });

    var commentable = false;
    $( "#comment-button" ).click(function() {
        if (!commentable){
            $('#comment-form').show("slow");
            $('#comment-button').html("<strong>Cancel</strong>");
            commentable = true;
        } else {
            $('#comment-form').hide("slow");
            $('#comment-button').html("Click <strong>here</strong> to comment on this poem!");
            commentable = false;
        }
    });
});