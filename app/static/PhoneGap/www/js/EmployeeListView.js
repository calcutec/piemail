

var EmployeeShortView = Backbone.View.extend({
    tagName:'li',

    className:'table-view-cell media',

    initialize: function () {

    },
    //events: {
    //    'click .seeEmployee':   'viewEmployee'
    //},
    //viewEmployee: function(e){
    //    e.preventDefault();
    //    console.log('sending for employee..')
    //},
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


    setEmployees:function(list) {
        this.employees = list;
        this.render();
    },

    render:function () {
        this.$el.empty();
        var self = this;
        if (!this.employees) {
            this.collection.fetch({
                success: function(collection) {
                    collection.each(function(Employee){
                        $('.table-view', this.el).append(new EmployeeShortView({model: Employee}).render().el);
                    });
                    window.localStorage.setItem("employees", JSON.stringify(
                        collection
                    ));
                    //employees = JSON.parse(window.localStorage.getItem("employees"))
                }
            });
        } else {
            this.$el.html(this.template(this.employees));
            return this;
        }
        return self
    }
});