var HomeView = Backbone.View.extend({

    initialize: function () {
        this.employees = new EmployeeCollection();
        this.listView = new EmployeeListView({collection: this.employees});
    },

    render: function () {
        this.$el.html(this.template());
        $('.content', this.el).append(this.listView.render().el);
        return this;
    },

    events: {
        "keyup .search-key":    "search",
        "keypress .search-key": "onkeypress"
    },

    search: function () {
        var key = $('.search-key').val();
        console.log(key);
        var service = new EmployeeService();
        var listView = this.listView;
        service.findByName(key).done(function(employees) {
            listView.setEmployees(employees);
        });
    },

    onkeypress: function (event) {
        if (event.keyCode === 13) { // enter key pressed
            event.preventDefault();
        }
    }
});