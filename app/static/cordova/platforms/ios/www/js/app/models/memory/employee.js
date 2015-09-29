define(function (require) {

    "use strict";

    var $                   = require('jquery'),
        Backbone            = require('backbone'),
        employees = JSON.parse(window.localStorage.getItem("employees")),

        findById = function (id) {
            var deferred = $.Deferred(),
                employee = null,
                l = employees.length,
                i;
            for (i = 0; i < l; i = i + 1) {
                if (employees[i].id === id) {
                    employee = employees[i];
                    break;
                }
            }
            deferred.resolve(employee);
            return deferred.promise();
        },

        findByName = function (searchKey) {
            var deferred = $.Deferred(),
                results = employees.filter(function (element) {
                    var fullName = element.firstName + " " + element.lastName;
                    return fullName.toLowerCase().indexOf(searchKey.toLowerCase()) > -1;
                });
            deferred.resolve(results);
            return deferred.promise();
        },

        findByManager = function (managerId) {
            var deferred = $.Deferred(),
                results = employees.filter(function (element) {
                    return managerId === element.managerId;
                });
            deferred.resolve(results);
            return deferred.promise();
        },


        Employee = Backbone.Model.extend({

            initialize: function () {
                this.reports = new ReportsCollection();
                this.reports.parent = this;
            },

            sync: function (method, model, options) {
                if (method === "read") {
                    findById(parseInt(this.id)).done(function (data) {
                        options.success(data);
                    });
                }
            }

        }),

        EmployeeCollection = Backbone.Collection.extend({

            model: Employee,

            search: function (key, listView) {
                findByName(key).done(function (data) {
                    listView.setEmployees(data);
                });
            },

            url: "http://www.netbard.com/employees",

            parse: function(response) {
                return response.employees;
            },

        }),

        ReportsCollection = Backbone.Collection.extend({

            model: Employee,

            sync: function (method, model, options) {
                if (method === "read") {
                    findByManager(this.parent.id).done(function (data) {
                        options.success(data);
                    });
                }
            }

        });

    return {
        Employee: Employee,
        EmployeeCollection: EmployeeCollection,
        ReportsCollection: ReportsCollection
    };

});