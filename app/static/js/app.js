//Testing bootstrap views
var Poem = Backbone.Model.extend({
  defaults: {
    author: 'any Text',
    header: 'any Text',
    writing_type: 'any Text',
    post: 'any Text'
  },
  validate: function(attrs, options){
    if ( !attrs.header ){
        alert('Your poem must have a header!');
    }
    if ( attrs.post.length < 10 ){
        alert('Your poem is too short!');
    }
  },
    urlRoot: '/poem/'
});

// Poem view
var PoemView = Backbone.View.extend({
    tagName: 'li', // defaults to div if not specified
    className: 'poem', // optional, can also set multiple like 'animal dog'
    id: 'bard', // also optional
    events: {
        'click .edit':   'editPoem',
        'click .delete': 'deletePoem'
    },
    savePoem: function(){
        this.model.save(null, {
            success: function(model, response){
                console.log('successful');
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
    // newTemplate: _.template('<%= name %> is <%= color %> and says <%= sound %>'), // inline template
    newTemplate: _.template($('#poemTemplate').html()), // external template
    initialize: function() {
        this.render(); // render is an optional function that defines the logic for rendering a template
        this.model.on('change', this.render, this); // calls render function once name changed
        this.model.on('destroy', this.remove, this); // calls remove function once model deleted
    },
    remove: function(){
        this.$el.remove(); // removes the HTML element from view when delete button clicked/model deleted
    },
    render: function() {
        // the below line represents the code prior to adding the template
        // this.$el.html(this.model.get('name') + ' is ' + this.model.get('color') + ' and says ' + this.model.get('sound'));
        this.$el.html(this.newTemplate(this.model.toJSON())); // calls the template
    }
});

// Poem collection
var PoemCollection = Backbone.Collection.extend({
    model: Poem,
    url: '/poems',
    parse: function(response){return response.myPoems;}
});

// View for all poems (collection)
var PoemsView = Backbone.View.extend({ // calling this PoemsView to distinguish as the view for the collection
    el: '#theForm',
    tagName: 'ul',
    events: {
        'click #open': 'openModal'
    },
    template: '<a id="open" class="btn">open modal</a>',
    openModal: function() {
        var view = new ModalView();
        var modal = new Backbone.BootstrapModal({
            content: view,
            title: 'modal header',
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

////The form
//var poemForm = Backbone.Form.extend({
//    template: _.template($('#formTemplate').html()),
//    schema: {
//        title:  'Text',
//        body:  'Text'
//    },
//    model: new Poem()
//});

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
//Could pass in tagnames and different forms to make generic
//Need to figure out how to do a submit button as well as a custom template
var ModalView = Backbone.View.extend({
    tagName: 'span id="theForm"',
    model: new Poem(),
    //view: new PoemView({model: this.model}),
    template: _.template($('#formTemplate').html()),
    events: {
        'submit form': 'submit'
    },

    render: function() {
        this.$el.html(this.template);
    },

    submit: function(e) {
        e.preventDefault();
        var $form = $('#poem-form');
        var data = JSON.stringify($form.serializeObject());
        this.model.set(data);
        var mypoemView = new PoemView({model: this.model});
        mypoemView.savePoem($form);
        //poemCollection.add(this.model);

        //var $form = $('#poem-form');
        ////var poem_text = $('#editable').html();
        ////$('#post').html(poem_text);
        //
        //$.post("/poem/", $form.serialize(),
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
        //        $("#main").append(result.new_post);
        //        this.template.commit();
        //        $("#myModal").modal('hide');
        //
        //    }
        //});
    }
});

$(document).ready(function() {
    var poemCollection = new PoemCollection();
    var poemsView = new PoemsView({collection: poemCollection});
    poemCollection.fetch({
        success: function() {
            poemsView.render();
        }
    })
});