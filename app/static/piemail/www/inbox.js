window.mailapp = $("#mailapp");
window.globalDate = new Date();

var Mail = Backbone.Model.extend( {
    defaults: {
        id: '',
        ordinal: '',
        subject: '',
        content: '',
        snippet: '',
        mailbody: '',
        timestamp: '',
        start: '',
        read: '',
        star: false,
        selected:false,
        archived:false,
        promotions:false,
        label: '',
        createdOn: "Note created on " + new Date().toISOString()
    },

    markRead: function() {
        this.save( {read: true } );
    },

    starMail: function() {
        this.save( { star: !this.get("star")} );
    },

    archive: function(){
        this.save( { archived: true, selected:false} );
    },

    moveToPromotions: function(){
        this.save( { promotions: true, selected:false} );
    },

    selectMail: function() {
        this.save( { selected: !this.get("selected")} );
    },

    setLabel: function(label){
        this.save( { label: label } );
    }

    //setOrdinal: function(ordinal){
    //    this.save( { ordinal: ordinal } );
    //}
});

var MailView = Backbone.View.extend({
    tagName: "div",
    className: "mail",

    template: _.template($("#mail-item").html()),

    events: {
        "click .mail-subject,.sender" : "markRead",
        "click .mail-snippet" : "getMail",
        "click .star" : "star",
        "click .check" : "select"
    },

    initialize: function() {
        this.model.bind('change', this.render, this);
        this.listenTo(this.model, 'removeme', this.remove);
    },

    render: function() {
        $(this.el).html( this.template(this.model.toJSON()) );
        return this;
    },

    //unrender: function(){
    //    $(this.el).remove();
    //},

    markRead: function() {
        this.model.markRead();
    },

    star: function() {
        this.model.starMail();
    },

    select: function(){
        this.model.selectMail();
    },

    getMail: function() {
        this.model.collection.getThread(this.model.get('id'));
    }
});

var MailList = Backbone.Collection.extend({
    model: Mail,
    url: '/inbox',

    localStorage: new Backbone.LocalStorage("threadList"),

    refreshFromServer : function(options) {
        return Backbone.ajaxSync('read', this, options);
    },

    //unread: function() {
    //    return _(this.filter( function(mail) { return !mail.get('read');} ) );
    //},

    inbox: function(){
        return _(this.filter( function(mail) { return !mail.get('archived');}));
    },

    promotionsbox: function(){
        return _(this.filter( function(mail) { return mail.get('promotions');}));
    },

    starred: function(){
        return _(this.filter( function(mail) { return mail.get('star');}));
    },

    unread_count: function() {
        return (this.filter ( function(mail) { return !mail.get('read');})).length;
    },

    //labelled:function(label){
    //    return _(this.filter( function(mail) { return label in mail.get('label') } ));
    //},

    starcount: function(){
        return (this.filter( function(mail) { return mail.get('star')})).length;
    },

    promotionscount: function(){
        return (this.filter( function(mail) { return mail.get('promotions')})).length;
    },

    //getThreads: function(){
    //    var threadArray = [];
    //    this.each(function(item){
    //        if(item.get('selected') == true){
    //          threadArray.push(item.get('id'));
    //        }
    //    }, this);
    //
    //},

    getThread: function(threadid){
        this.each(function(model){
            model.trigger('removeme');
        });
        $('#visualization').html('');
        var gridlist = new GridList();
        gridlist.getThread(threadid, function(){
            $('.inboxfunctions').addClass("hidden");
            $('.gridfunctions').removeClass("hidden");
            window.newgridview = new GridView({collection: self})
        });
    },

    search: function(word){
        if (word=="") return this;

        var pat = new RegExp(word, 'gi');
        return _(this.filter(function(mail) { 
            return pat.test(mail.get('subject')) || pat.test(mail.get('sender')); }));
    }
});

var InboxView = Backbone.View.extend({
    summarytemplate: _.template($("#summary-tmpl").html()),
    el: window.mailapp,

    initialize: function(){
        this.collection.bind('change', this.renderSideMenu, this);
        this.listenTo(this.collection, 'reset', this.removeAll);
        this.render(this.collection);
        this.renderSideMenu();
    },

    events: {
        "change #labeler": "applyLabel",
        "click #markallread": "markallread",
        "click #archive": "archive",
        "click #gridview": "gridview",
        "click #allmail": "allmail",
        "click #inbox": "inbox",
        "click #promotionsbox": "promotionsbox",
        "click #movetopromotions": "movetopromotions",
        "click #starred": "starred",
        "keyup #search" : "search"
    },

    search: function(){
        this.render(this.collection.search($("#search").val()));
    },

    starred: function(){
        this.render(this.collection.starred());
    },

    inbox: function(){
        this.render(this.collection.inbox());
    },

    promotionsbox: function(){
        this.render(this.collection.promotionsbox());
    },

    allmail: function(){
        this.render(this.collection);
    },

    markallread : function(){
        this.collection.each(function(item){
          item.markRead();
        }, this);
    },

    applyLabel: function(){
        var label = $("#labeler").val();
        this.collection.each(function(item){
            if(item.get('selected') == true){
              item.setLabel(label);
            }
        }, this);
    },

    archive: function(){
        this.collection.each(function(item){
            if(item.get('selected') == true){
              item.archive();
            }
        }, this);
        this.render(this.collection.inbox());
    },

    movetopromotions: function(){
        this.collection.each(function(item){
            if(item.get('selected') == true){
              item.moveToPromotions();
            }
        }, this);
        this.render(this.collection.promotionsbox());
    },

    render: function(records){
        $('#mail-list', this.el).html('');
        var self = this;
        records.each(function(item){
            self.addOne(item);
        }, this);
    },

    renderSideMenu: function(){
        $("#sidemenu").html( this.summarytemplate({
            'inbox': this.collection.unread_count(),
            'starred':this.collection.starcount(),
            'promotions':this.collection.promotionscount()
        }));
    },

    addOne: function (mail) {
        var itemView = new MailView({ model: mail});
        $('#mail-list', this.el).append(itemView.render().el);
    },

    removeAll: function(){
        this.$el.empty()
    }
});

var GridList = Backbone.Collection.extend({
    model: Mail,
    url: '/threadslist',
    //groupCount: threadArray.length,
    groupCounter: 0,

    localStorage: new Backbone.LocalStorage("messageList"),

    refreshFromServer : function(options) {
        return Backbone.ajaxSync('read', this, options);
    },

    getThread: function (threadid, callback) {
        window.self = this;
        var request = $.ajax({
            url: "/threadslist",
            data: { "threadid" : threadid }
        });
        request.done(function( response ) {
            var itemcount = response['currentMessageList'].length;
            response['currentMessageList'].forEach(function (message, i){
                var mailitem = new Mail({
                    id: message.id,
                    group: window.self.groupCounter,
                    sender: message.sender,
                    subject:message.subject,
                    ordinal:message.ordinal,
                    snippet: message.snippet + "...",
                    mailbody: message.body,
                    formattedDate:message.date,
                    timestamp:message.timestamp,
                    start:message.timestamp,
                    read: message.read,
                    promotions: message.promotions,
                    social: message.social
                });
                window.self.add(mailitem);
                mailitem.save();
                if (i == itemcount - 1){
                    callback();
                }
            });
        });
        request.fail(function( jqXHR, textStatus ) {
            callback( "Request failed: " + textStatus );
        });
    }
});

var GridView;
GridView = Backbone.View.extend({
    el: window.mailapp,
    emailreplytemplate: _.template($("#emailreply-template").html()),

    initialize: function () {
        this.render();
    },

    events: {
        "click #fit": "fitall",
        "click #moveTo": "moveto",
        "click #visualization": "handleTimelineEvents",
        "click #window1": "setwindow",
        "click #previousweek": "previousweek"
    },

    render: function () {
        this.timeline = new vis.Timeline(document.getElementById('visualization'));
        this.timeline.setOptions(this.timelineoptions);
        var groupDataSet = new vis.DataSet();
        var itemDataSet = new vis.DataSet();
        itemDataSet.add(this.collection.toJSON());
        groupDataSet.add({
            id: 0,
            value: this.collection.models[0].get('timestamp'),
            content: "<span class='myGroup' style='color:#97B0F8; " +
            "max-width:200px; white-space:wrap'>" +
            this.truncateTitle(this.collection.models[0].get('subject')) + "</span>"
        });
        this.timeline.setGroups(groupDataSet);
        this.timeline.setItems(itemDataSet);
        $('body').append('<div id="overlay"></div>');
    },

    truncateTitle: function (title) {
        var length = 25;
        if (title.length > length) {
            title = title.substring(0, length) + '...';
        }
        return title;
    },

    handleTimelineEvents: function (event) {
        if (typeof this.collection.timeline === 'undefined') {
            console.log("Timeline not yet defined..");
        } else {
            var props = this.collection.timeline.getEventProperties(event);
            if (typeof(props.item) === 'undefined' || props.item === null) {
                if (props.event.target.id == "emailreplyclose") {
                    $('#emailreply, #emailreplyclose, #overlay').fadeOut(300);
                } else {
                    console.log('no props item')
                }

            } else {
                this.renderemailbody(props);
            }
        }
    },

    fitall: function () {
        this.timeline.fit();
    },

    moveto: function () {
        this.timeline.moveTo('2015-10-14');
    },

    setwindow: function () {
        var today = new Date();
        var numberOfDaysToAdd = 2;
        var limitdate = today.setDate(today.getDate() + numberOfDaysToAdd);
        var lastWeek = new Date(today.getTime() - 1000 * 60 * 60 * 24 * 7);
        this.timeline.setWindow(lastWeek, limitdate);
    },

    previousweek: function () {
        var begindate = null;
        var previous = null;
        if (begindate) {
            begindate = previous;
        } else {
            begindate = new Date();
        }
        previous = new Date(begindate.getTime() - 1000 * 60 * 60 * 24 * 7);
        var previous2 = new Date(previous.getTime() - 1000 * 60 * 60 * 24 * 7);
        this.timeline.setWindow(previous2, previous)
    },

    renderemailbody: function (props) {
        var currentid = props.item;
        var emailbody = this.emailreplytemplate({'id': currentid});
        var overlay = document.getElementById('overlay');
        overlay.style.opacity = .7;
        $('#visualization').append(emailbody);
        $('#overlay, #emailreply').fadeIn(300);
    },

    timelineoptions: {
        showCurrentTime: true,
        zoomable: true,
        zoomMin: 1000 * 60 * 60 * 24,  // one day in milliseconds
        zoomMax: 1000 * 60 * 60 * 24 * 31,  // about one month in milliseconds
        max: window.globalDate.setDate(window.globalDate.getDate() + 7),
        zoomKey: 'altKey',
        type: 'point',
        margin: {
            item: {
                horizontal: 5,
                vertical: 5
            },
            axis: 5
        },
        stack: true,
        template: _.template($("#mail-plot").html()),
        orientation: {
            axis: "top",
            item: "top"
        },
        minHeight: '250px',
        order: function customOrder(a, b) {
            return a.ordinal - b.ordinal;
        }
    }
});

startapp = function () {
    $('#mailapp').removeClass("hidden");
    $('.inboxfunctions').removeClass("hidden");
    window.threadslist = new MailList();

    window.threadslist.refreshFromServer({
        success: function(freshData) {
            window.threadslist.set(freshData['newcollection']);
            window.threadslist.forEach(function(model){model.save()});
            window.currentInbox = new InboxView({collection: window.threadslist});
        }
    });
};

$( document ).ready(function() {
    startapp();
});