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
        rawtimestamp: '',
        start: '',
        unread: false,
        star: false,
        selected:false,
        inbox:false,
        primary:false,
        social:false,
        promotions:false,
        updates:false,
        forums:false,
        archived:false,
        sent:false,
        label: '',
        createdOn: "Note created on " + new Date().toISOString()
    },


    move: function(value){
        var obj = {};
        obj['category'] = value;
        obj['selected'] = false;
        if(value == "archived"){
            obj['inbox'] = false;
        }
        this.save( obj );
    },

    markRead: function() {
        this.save( {unread: false, selected:false} );
    },

    starMail: function() {
        this.save( { star: !this.get("star")} );
    },

    selectMail: function() {
        this.save( { selected: !this.get("selected")} );
    },

    setLabel: function(label){
        this.save( { label: label } );
    }
});

var MailView = Backbone.View.extend({
    tagName: "div",
    className: "mail",
    template: Handlebars.getTemplate("mail-item"),
    timelineTemplate: Handlebars.getTemplate("timeline"),
    fullmailTemplate: Handlebars.getTemplate("fullmailTemplate"),

    events: {
        //"click .mail-subject,.sender" : "markRead",
        "click .mail-snippet, .mail-subject, .sender" : "getMail",
        "click .star" : "star",
        "click .check" : "select",
        "click .closepreview" : "closepreview",
        "click .showmailtimeline" : "showMailTimeLine"
    },

    initialize: function() {
        this.model.bind('change', this.render, this);
        this.listenTo(this.model, 'removeme', this.remove);
    },

    render: function() {
        $(this.el).html( this.template(this.model.toJSON()) );
        return this;
    },

    unrender: function(){
        $(this.el).remove();
    },

    markRead: function(e) {
        if(typeof(e) === "undefined"){
            this.model.markRead();
        } else {
            e.preventDefault();
            this.model.markRead();
        }
    },

    star: function(e) {
        e.preventDefault();
        this.model.starMail();
    },

    closepreview: function(e) {
        e.preventDefault();
		this.render();
    },

    select: function(){
        this.model.selectMail();
    },

    getMail: function(e) {
        e.preventDefault();
        this.markRead();
        var currentitem = $(this.el);
        currentitem.html('');
        currentitem.html(this.fullmailTemplate(this.model.toJSON()));
        window.gridlist = new GridList();
        window.gridlist.showThread(this.model.id);
    },

    showMailTimeLine: function(e) {
        e.preventDefault();
        this.markRead();
        var currentitem = $(this.el);
        currentitem.html('');
        currentitem.html(this.timelineTemplate());
        window.newgridview = new GridView({collection: window.gridlist, el:currentitem});
    }
});

var MailList = Backbone.Collection.extend({
    model: Mail,
    url: '/mailbody',

    localStorage: new Backbone.LocalStorage("threadList"),

    refreshFromServer : function(options) {
        return Backbone.ajaxSync('read', this, options);
    },

    show: function(value, currentlyviewed){
        if(typeof(currentlyviewed) === "undefined" || currentlyviewed == "inbox"){
            if(value=="inbox"||value=="star"||value=="unread") {
                return _(this.filter(function (mail) { return mail.get(value) }));
            } else if(value=="onlyread") {
                return _(this.filter(function (mail) { return !mail.get('unread') }));
            } else {
                return _(this.filter( function(mail) { return mail.get('category') === value}));
            }
        } else {
            if(value=="unread"||value=="star") {
                return _(this.filter(function (mail) {
                    return mail.get(value) && mail.get('category') === currentlyviewed
                }));
            } else if(value=="onlyread") {
                return _(this.filter(function (mail) {
                    return !mail.get('unread') && mail.get('category') === currentlyviewed
                }));
            }
        }
    },

    categorycounts: function(category) {
        return (this.filter( function(mail) { return mail.get('category') === category})).length;
    },

    othercounts: function(item){
        return (this.filter( function(mail) { return mail.get(item)})).length;
    },

    search: function(word){
        if (word=="") return this;
        var pat = new RegExp(word, 'gi');
        return _(this.filter(function(mail) {
            return pat.test(mail.get('subject')) || pat.test(mail.get('sender')); }));
    },

    comparator: function(mail){
        return -mail.get('rawtimestamp');
    }
});

var InboxView = Backbone.View.extend({
    summarytemplate: Handlebars.getTemplate("summary-tmpl"),
    el: window.mailapp,

    initialize: function(){
        this.listenTo(this.collection, 'change', this.renderSideMenu);
        this.listenTo(this.collection, 'reset', this.removeAll);
        this.render(this.collection);
        this.renderSideMenu();
    },

    events: {
        "keyup #search" : "search",
        "click #inbox": "dispatchevent",
        "click #sent": "dispatchevent",
        "click #primary": "dispatchevent",
        "click #social": "dispatchevent",
        "click #promotions": "dispatchevent",
        "click #updates": "dispatchevent",
        "click #forums": "dispatchevent",
        "click #archived": "dispatchevent",
        "click #star": "dispatchevent",
        "click #unread": "dispatchevent",
        "click #allmail": "dispatchevent",
        "change #actions": "applyAction",
        "click .refresh": "refresh",
        "click #gridview": "gridview",
        "click #signout": "signout",
        "click #compose": "compose",
        "click #trash": "trash"
    },

    compose: function(){
        alert('not yet implemented');
    },

    trash: function(){
        alert('not yet implemented');
    },

    search: function(){
        this.render(this.collection.search($("#search").val()));
    },

    markallasread : function(){
        this.collection.each(function(item){
          item.markRead();
        }, this);
    },

    markasread: function(){
        this.collection.each(function(item){
            if(item.get('selected') == true){
              item.markRead();
            }
        }, this);
    },

    applyAction: function(){
        var action = $(':selected', $('#actions')).parent().attr('label');
        var value =  $("#actions").val();
        var currentlyviewed = $('.active').find('a').attr('id');
        $('#actions').val('0');
        if(action == "Show"){

            if(value == "Only Unread"){
                this.show('unread', currentlyviewed);
            } else if(value == "Only Read"){
                this.show('onlyread', currentlyviewed);
            } else {
                this.show('star', currentlyviewed);
            }
        } else if(action == "Move"){
            if(value == "Archive"){
                this.move('archived', currentlyviewed);
            } else {
                this.move(value.toLowerCase(), currentlyviewed);
            }
        } else if (action == "Label"){
            this.applyLabel(value);
        } else if (action == "Mark"){
            if(value == "Mark all as Read"){
                this.markallasread();
            } else if(value == "Mark selected as Read") {
                this.markasread();
            }
        }
    },

    dispatchevent: function(event){
        var eventid = event.currentTarget.id;
        window.active = $(event.currentTarget).parent();
        window.active.addClass('active');
        $('li').not(window.active).removeClass('active');
        this.show(eventid);
    },

    show: function(value, currentlyviewed){
        if(value == "allmail"){
            this.render(this.collection);
        } else {
            this.render(this.collection.show(value, currentlyviewed));
        }
    },

    move: function(value, currentlyviewed){
        this.collection.each(function(item){
            if(item.get('selected') == true){
              item.move(value);
            }
        }, this);
        this.render(this.collection.show(currentlyviewed));
        this.renderSideMenu();
    },

    applyLabel: function(value){
        this.collection.each(function(item){
            if(item.get('selected') == true){
              item.setLabel(value);
            }
        }, this);
    },

    render: function(records){
        $('#mail-list', this.el).html('');
        var self = this;
        records.each(function(item){
            self.addOne(item);
        }, this);
    },
    renderSideMenu: function(){
        var currentlyactive = $('.active');
        $("#sidemenu").html( this.summarytemplate({
            'inbox': this.collection.othercounts('inbox'),
            'primary': this.collection.categorycounts('primary'),
            'social':this.collection.categorycounts('social'),
            'promotions':this.collection.categorycounts('promotions'),
            'updates':this.collection.categorycounts('updates'),
            'forums':this.collection.categorycounts('forums'),
            'archived':this.collection.categorycounts('archived'),
            'sent':this.collection.categorycounts('sent'),
            'starred':this.collection.othercounts('star'),
            'unread': this.collection.othercounts('unread')
        }));
        if (typeof(currentlyactive)[0] === 'undefined'){
            $('#inbox').parent().addClass('active');
        } else {
            $('#'+currentlyactive.find('a').attr('id')).parent().addClass('active');
        }
    },

    addOne: function (mail) {
        var itemView = new MailView({ model: mail});
        $('#mail-list', this.el).append(itemView.render().el);
    },

    removeAll: function(){
        this.$el.empty()
    },

    signout: function(){
        $.getJSON($SCRIPT_ROOT + 'signmeout', function(data) {
            window.location.replace(data.redirect_url);
        });
        return false;
    },

    refresh: function(){
        window.location.replace("/");
    }
});

var GridList = Backbone.Collection.extend({
    model: Mail,
    url: '/threadslist',
    localStorage: new Backbone.LocalStorage("messageList"),

    refreshFromServer : function(options) {
        return Backbone.ajaxSync('read', this, options);
    },

    showThread: function (threadid, callback) {
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
                    timestamp:message.timestamp,
                    start:message.timestamp,
                    read: message.read,
                    promotions: message.promotions,
                    social: message.social
                });
                window.self.add(mailitem);
                mailitem.save();
                if (i == itemcount - 1){
                    console.log("all done")
                }
            });
        });
        request.fail(function( jqXHR, textStatus ) {
            console.log("Request failed: " + textStatus)
        });
    }
});

var GridView = Backbone.View.extend({
    emailreplytemplate: Handlebars.getTemplate("email-reply"),

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
        var itemDataSet = new vis.DataSet();
        itemDataSet.add(this.collection.toJSON());
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
        if (typeof this.timeline === 'undefined') {
            console.log("Timeline not yet defined..");
        } else {
            var props = this.timeline.getEventProperties(event);
            if (typeof(props.item) === 'undefined' || props.item === null) {
                if (props.event.target.id == "emailreplyclose") {
                    $('#emailreply, #emailreplyclose, #overlay').fadeOut(300);
                } else {
                    console.log('no props item')
                }

            } else {
                //this.renderemailbody(props);
                console.log('feature under construction')
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
        $('body').append(emailbody);
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
        template: Handlebars.getTemplate("mail-plot"),
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
    window.threadslist = new MailList(appInitialData);
    window.currentInbox = new InboxView({collection: window.threadslist});
    window.threadslist.refreshFromServer({
        success: function(freshData) {
            window.threadslist.set(freshData['newcollection']);
        },
        fail: function(error) {
            console.log(error);
        }
    });
};


$( document ).ready(function() {
    startapp();
});