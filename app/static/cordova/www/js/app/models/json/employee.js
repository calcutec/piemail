define(function (require) {

    "use strict";

    var $                   = require('jquery'),
        Backbone            = require('backbone'),

        Employee = Backbone.Model.extend({

            urlRoot: "http://www.netbard.com/employees",

            initialize: function () {
                this.reports = new EmployeeCollection();
                this.reports.url = this.urlRoot + "/" + this.id + "/reports";
            }

        }),

        EmployeeCollection = Backbone.Collection.extend({

            model: Employee,

            url: "http://www.netbard.com/employees",
            parse: function(response)
                {
                    return response.employees;
                }

        });

    return {
        Employee: Employee,
        EmployeeCollection: EmployeeCollection
    };

});