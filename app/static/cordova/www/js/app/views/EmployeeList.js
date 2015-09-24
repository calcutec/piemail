define(function (require) {

    "use strict";

    var $                   = require('jquery'),
        _                   = require('underscore'),
        Backbone            = require('backbone'),
        tpl                 = require('text!tpl/EmployeeList.html'),

        template = _.template(tpl);

    return Backbone.View.extend({

        initialize: function () {
            this.render();
            this.collection.on("reset", this.render, this);
        },

        setEmployees:function(matchedEmployees) {
            this.matchedEmployees = matchedEmployees;
            this.render();
        },

        render:function () {
            this.$el.empty();
            if (!this.matchedEmployees) {
                this.$el.html(template({employees: this.collection.toJSON()}));
                return this;
            } else {
                this.$el.html(template({employees:this.matchedEmployees}));
                return this;
            }
        }

        //render: function () {
        //    this.$el.html(template({employees: this.collection.toJSON()}));
        //    return this;
        //}

    });

});