// defines the namespace
window.App = {  // top level namespace is declared on the window
  Models: {},
  Collections: {},
  Views: {},
  Router: {}
};

// Post model
App.Models.Post = Backbone.Model.extend({
  urlRoot: '/detail/portfolio/',
  defaults: {
    header: '',
    body: ''
  },
  validate: function(attrs){
    if (!attrs.header){
        alert('Your post must have a header!');
    }
    if (attrs.body.length < 2){
        alert('Your post must have more than one letter!');
    }
  },
  addToCollection: function(){
    alert(this.get('header') + ' is the title of my post.');
  }
});

// Post view
App.Views.Post = Backbone.View.extend({
  tagName: 'article', // defaults to div if not specified
  //className: 'exampleClass', // optional, can also set multiple like 'exampleClassII'
  //id: 'exampleID', // also optional
  events: {
    'click .edit':   'editPost',
    'click .delete': 'deletePost'
  },
  editPost: function(){
    var newPost = prompt("New post name:", this.model.get('header')); // prompts for new name
    if (!newPost)return;  // no change if user hits cancel
    this.model.set('header', newPost); // sets new name to model
  },
  deletePost: function(){
    this.model.destroy(); // deletes the model when delete button clicked
  },
  newTemplate: _.template($('#postTemplate').html()), // external template
  initialize: function(){
    //this.render(); // render is an optional function that defines the logic for rendering a template
    //this.model.on('change', this.render, this); // calls render function once name changed
    this.model.bind("change:header", this.updateTitle, this);
    this.model.on('destroy', this.remove, this); // calls remove function once model deleted
  },
  remove: function(){
    this.$el.remove(); // removes the HTML element from view when delete button clicked/model deleted
  },
  updateTitle: function(model, val) {
      this.el.getElementsByTagName('a')[0].innerHTML = val;
      model.save();
  },
  render: function(){
    this.$el.html(this.newTemplate(this.model.toJSON())); // calls the template
    $("#main").prepend(this.el);
  }
});

App.Views.PoemView = Backbone.View.extend({
  initialize: function(){
    this.model.bind("change:name", this.updateName, this);
  },

  updateName: function(model, val){
    this.el.text(val);
  }
});

// Post collection
App.Collections.Post = Backbone.Collection.extend({
  model: App.Models.Post,
  url: '/poetry/workshop/',
  parse: function(response){return response.myPoems;},
  clear_all: function(){
    var model;
    while (model = this.first()) {
      model.destroy();
    }
  }
});

// View for all posts (collection)
App.Views.Posts = Backbone.View.extend({ // plural to distinguish as the view for the collection
  //initialize: function(){
  //  this.collection;
  //},
  attachToView: function(){
    this.el = $("#poem-list");
    var self = this;
    $("article").each(function(){
      var poemEl = $(this);
      var id = poemEl.attr("data-id");
      var poem = self.collection.get(id);
      new App.Views.Post({
        model: poem,
        el: poemEl
      });
    });
  },
  render: function(){
    this.collection.each(function(Post){
      var postView = new App.Views.Post({model: Post});
      $("#main").prepend(postView.el);
    });
  }
});


// Backbone router
App.Router = Backbone.Router.extend({
  routes: { // sets the routes
    '':         'index', // http://tutorial.com
    'edit/:id': 'edit' // http://tutorial.com/#edit/7
  },
  // the same as we did for click events, we now define function for each route
  index: function(){
    console.log('index route');
  },
  edit: function(id){
    console.log('edit route with id: ' + id);
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

App.Views.ModalDisplay = Backbone.View.extend({
    el: '#myPortfolio',
    events: {
        'click #open': 'openModal'
    },
    template: '<h1><button type="button" id="open" class="btn btn-info btn-lg">Create Poem</button></h1>',
    openModal: function() {
        var view = new App.Views.ModalView();
        var modal = new Backbone.BootstrapModal({
            content: view,
            title: 'modal header',
            animate: true,
            okText: 'Submit New Post',
            okCloses: true,
            enterTriggersOk: true
        }).open(function(){
            var poem_text = $('#editable').html();
            $('#show-form').html(poem_text);
            var $form = $('#poem-form');
            var data = $form.serializeObject();
            var newPostModel = new App.Models.Post(data);
            newPostModel.save(null, {
                success: function (model, response) {
                    new App.Views.Post({model:model}).render();
                    return response;
                },
                error: function () {
                    alert('your poem did not save properly..')
                }
            });

        });
    },
    render: function() {
        this.$el.html(this.template);
        console.log('main rendered');
        return this;
    }
});

App.Views.ModalView = Backbone.View.extend({
    template: _.template($('#formTemplate').html()),
    events: {
        'submit form': 'submit'
    },
    render: function() {
        this.$el.html(this.template);
        console.log('modal rendered');
        return this;
    }
});

$(document).ready(function() {

    ////adding individual models to collection
    //    var chihuahua = new App.Models.Post({header: 'Sugar', post: 'This this the name of my chihuahua'});
    //    var chihuahuaView = new App.Views.Post({model: chihuahua});
    //    var postCollection = new App.Collections.Post(); // only need to create the collection once
    //    postCollection.add(chihuahua);

    ////adding multiple models to collection////
    //    var postCollection = new App.Collections.Post([
    //     {
    //       header: 'Sugar',
    //       post: 'That is the name of my chihuahua',
    //     },
    //     {
    //       header: 'Gizmo',
    //       post: 'That is the name of my beagle'
    //     }
    //    ]);
    //    var postsView = new App.Views.Posts({collection: postCollection});
    //    postsView.render();
    //    sessionStorage.setItem('postCollection', JSON.stringify(postCollection));


    ////Retrieving models from flask database////
    //    postCollection.fetch({
    //        success: function() {
    //            postsView.render();
    //        }
    //    })

    ////Bootstrapping flask models on load////
    //    postCollection = new App.Collections.Post();
    //    $(function () {
    //        $('Article').each(function() {
    //            postCollection.add(new App.Models.Post($(this).data()));
    //        });
    //        postsView = new App.Views.Posts({collection: postCollection});
    //        //postsView.render()
    //    });

    new App.Router;
    Backbone.history.start(); // start Backbone history

    var modalDisplayView = new App.Views.ModalDisplay();
    modalDisplayView.render();

    var postCollection = new App.Collections.Post();
    var articleSelector = $("article");
    articleSelector.each(function() {
        postCollection.add(new App.Models.Post($(this).data()));
    });
    var poemListView = new App.Views.Posts({collection: postCollection});
    poemListView.attachToView();
    //postCollection.get(112).set({title: "No Longer Bob"});
});