define(function (require) {

    "use strict";

    var $                   = require('jquery'),
        _                   = require('underscore'),
        Backbone            = require('backbone'),
        EmployeeListView    = require('app/views/EmployeeList'),
        models              = require('app/models/employee'),
        tpl                 = require('text!tpl/Home.html'),
        employeeCollection = new models.EmployeeCollection(),

        template = _.template(tpl);

    return Backbone.View.extend({
        initialize: function () {
            var self = this;
            employeeCollection.fetch({
                success: function(collection) {
                    window.localStorage.setItem("employees", JSON.stringify(
                        collection.toJSON()
                    ));
                    self.render();
                }
            });
        },

        render: function () {
            this.$el.html(template());
            this.listView = new EmployeeListView({collection: employeeCollection, el: $(".scroller", this.el)});
            return this;
        },

        events: {
            "keyup .search-key":    "search",
            "keypress .search-key": "onkeypress"
        },

        search: function (event) {
            var key = $('.search-key').val();
            employeeCollection.search(key, this.listView);
        },

        onkeypress: function (event) {
            if (event.keyCode === 13) { // enter key pressed
                event.preventDefault();
            }
        }

    });

});