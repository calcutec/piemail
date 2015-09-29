require.config({

    //baseUrl: 'js/lib', //Phonegap
    //baseUrl: '/static/cordova/www/js/lib', //Flask Dev
    baseUrl: 'https://s3.amazonaws.com/netbardus/cordova/www/js/lib', //Flask Prod


    paths: {
        app: '../app',
        tpl: '../tpl'
    },

    map: {
        '*': {
            'app/models/employee': 'app/models/memory/employee'
        }
    },

    shim: {
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        'underscore': {
            exports: '_'
        }
    },
    config: {
        text: {
          useXhr: function (url, protocol, hostname, port) {
            // allow cross-domain requests
            // remote server allows CORS
            return true;
          }
        }
    }
});

require(['jquery', 'backbone', 'app/router'], function ($, Backbone, Router) {

    var router = new Router();

    $("body").on("click", ".back-button", function (event) {
        event.preventDefault();
        window.history.back();
    });

    Backbone.history.start();
});