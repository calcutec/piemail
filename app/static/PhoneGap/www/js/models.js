var Employee = Backbone.Model.extend({
    urlRoot: "/employees"
});

var EmployeeCollection = Backbone.Collection.extend({
    model: Employee,
    url: "/employees",
    parse: function(response)
    {
        return response.employees;
    }
});
