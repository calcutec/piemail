var Poem = Backbone.Model.extend({
  defaults: {
    author: 'TBD',
    header: 'any Text',
    writing_type: 'any Text',
    post: 'any Text'
  },
  validate: function(attrs, options){
    if ( !attrs.header ){
        alert('Your poem must have a header!');
    }
    if ( attrs.post.length < 2 ){
        alert('Your poem is too short!');
    }
  },
    urlRoot: '/detail/portfolio/'
});

////Destroy Post
//    $( "#delete-button" ).click(function() {
//        var post_id = $('.post-id').html();
//        $.ajax({
//            url: '/detail/' + post_id,
//            type: 'DELETE',
//            success: function(result) {
//                if(result.iserror) {
//                    alert("An error occurred while deleting the last item..")
//                }else {
//                    // When backbone is complete, remove poem from the current DOM
//                    location.href = "/poetry/portfolio"
//                }
//            }
//        });
//    });


// Poem view
var PoemView = Backbone.View.extend({
    tagName: 'li', // defaults to div if not specified
    className: 'poem', // optional, can also set multiple like 'animal dog'
    id: 'bard', // also optional
    events: {
        'click .edit':   'editPoem',
        'click #delete-button': 'deletePoem'
    },
    savePoem: function(){
        this.model.save(null, {
            success: function(model, response){
                console.log('successful');
                $("#main").prepend(response.new_poem);
                $(".modal").modal('hide');
            },
            error: function(model, response){
                console.log('unsuccessful');
            },
            wait: true // wait for the server response before saving
        });
    },
    editPoem: function(){
        var newPoem = prompt("New poem title:", this.model.get('header')); // prompts for new name
        if (!newPoem)return;  // no change if user hits cancel
        this.model.set('header', newPoem); // sets new title to model
        this.model.save()
    },
    deletePoem: function(){
        this.model.destroy(); // deletes the model when delete button clicked
    },
    newTemplate: _.template('<%= header %>, written by <%= author %>, reads as follows: <%= post %>'), // inline template
    //newTemplate: _.template($('#poemTemplate').html()), // external template
    initialize: function() {
        this.render(); // render is an optional function that defines the logic for rendering a template
        this.model.on('change', this.render, this); // calls render function once name changed
        this.model.on('destroy', this.remove, this); // calls remove function once model deleted
    },
    remove: function(){
        this.$el.remove(); // removes the HTML element from view when delete button clicked/model deleted
    },
    render: function() {
        this.$el.html(this.newTemplate(this.model.toJSON())); // calls the template
        alert("render function for PoemView has just been called")
    }
});

// Poem collection
var PoemCollection = Backbone.Collection.extend({
    model: Poem,
    url: '/poetry/workshop/',
    parse: function(response){return response.myPoems;}
});

// View for all poems (collection)
var PoemsView = Backbone.View.extend({ // calling this PoemsView to distinguish it from the view for the model
     el: '.page',
     tagName: 'ul',
     events: {
         'click #openPoemModal': 'openModal'
     },
     openModal: function() {
         var view = new ModalView();
         var modal = new Backbone.BootstrapModal({
             content: view,
             title: 'Create Poem',
             animate: true
         });
         modal.open(function(){ console.log('clicked OK') });
     },
     initialize: function(){
         this.collection;
     },
     render: function(){
         this.$el.html(this.template);
         this.collection.each(function(Poem){
             var poemView = new PoemView({model: Poem});
             $('#main').append(poemView.el);
         });
     }
 });


$.fn.serializeObject = function()
{
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

//Puts the form for a poem into a modal view
//Need to pass in different forms and models to make generic
var ModalView = Backbone.View.extend({
    tagName: 'span id="theForm"',
    model: new Poem(),
    template: _.template($('#formTemplate').html()),
    events: {
        'submit form': 'submit'
    },

    render: function() {
        this.$el.html(this.template);
    },

    submit: function(e) {
        e.preventDefault();
        var poem_text = $('#editable').html();
        $('#show-form').html(poem_text);
        var $form = $('#poem-form');
        var data = JSON.stringify($form.serializeObject());
        this.model.set($form.serializeObject());
        var mypoemView = new PoemView({model: this.model});
        mypoemView.savePoem(data);
        poemCollection.add(this.model);

        //$.post("/detail/", $form.serialize(),
        //    function(data) {
        //    var result = $.parseJSON(data);
        //    var error_header = $("#error_header");
        //    var error_post = $("#error_post");
        //    var error_writing_type = $("#error_writing_type");
        //    error_header.text("");
        //    error_post.text("");
        //    error_writing_type.text("");
        //
        //    if(result.iserror) {
        //        if(result.header!=undefined) error_header.text(result.header[0]);
        //        if(result.post!=undefined) error_post.text(result.post[0]);
        //        if(result.writing_type!=undefined) error_writing_type.text(result.writing_type[0]);
        //    }else if (result.savedsuccess) {
        //        $("#main").prepend(result.new_poem);
        //        $(".modal").modal('hide');
        //        this.template.commit();
        //    }
        //});
    }
});

//var poemCollection = new PoemCollection();
//
//$(function () {
//    $('.comment').each(function() {
//        poemCollection.add(new Poem($(this).data()));
//    });
//});
//
//var poemsView = new PoemsView({collection: poemCollection});




//poemCollection.fetch({
//    success: function() {
//        poemsView.render();
//    }
//})