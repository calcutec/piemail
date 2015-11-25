// greater than or equal to
Handlebars.registerHelper('ge', function( a, b ){
	var next =  arguments[arguments.length-1];
	return (a >= b) ? next.fn(this) : next.inverse(this);
});