var EmployeeShortView = Backbone.View.extend({
    initialize: function () {

    },
    events: {
        'click .seeEmployee':   'viewEmployee'
    },
    viewEmployee: function(e){
        e.preventDefault();
        console.log('sending for employee..')
    },
    render: function(){
        this.$el.html(this.template(this.model.toJSON())); // calls the template
        return this
    }
});

var EmployeeListView = Backbone.View.extend({

    tagName:'ul',

    className:'table-view',

    initialize:function (options) {
        var self = this;
        this.collection.on("reset", this.render, this);
    },

    render:function () {
        this.$el.empty();
        var self = this;
        this.collection.fetch({
            success: function(collection) {
                collection.each(function(Employee){
                    $('.table-view', this.el).append(new EmployeeShortView({model: Employee}).render().el);
                });
            }
        });
        return self

    }
});