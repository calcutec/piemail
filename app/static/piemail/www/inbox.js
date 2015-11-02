var Mail = Backbone.Model.extend( {
    defaults: {
        id: '',
        ordinal: '',
        subject: '',
        snippet: '',
        mailbody: '',
        timestamp: '',
        start: '',
        read: false,
        star: false,
        selected:false,
        archived:false,
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

    selectMail: function() {
        this.save( { selected: !this.get("selected")} );
    },

    setLabel: function(label){
        this.save( { label: label } );
    }
});

var MailView = Backbone.View.extend({
    tagName: "div",
    className: "topcoat-grid__column--auto",

    template: _.template($("#mail-item").html()),

    events: {
        // "click .mail-subject,.sender,.mail-snippet" : "markRead",
        "click .mail-subject,.sender,.mail-snippet" : "getMail",
        "click .star" : "star",
        "click .check" : "select"
    },

    initialize: function() {
        //this.listenTo(this.model, 'change', this.render);
        //this.listenTo(this.model, 'destroy', this.remove, this.unrender())
    },

    render: function() {
        $(this.el).html( this.template(this.model.toJSON()) );
        return this;
    },

    unrender: function(){
        $(this.el).remove();
    },

    markRead: function() {
        this.model.markRead();
    },

    getMail: function() {
        this.model.collection.getThreads([this.model.get('id')]);
    },

    star: function() {
        this.model.starMail();
    },

    select: function(){
        this.model.selectMail();
    }
});

var MailList = Backbone.Collection.extend({
    initialize: function(models, options) {
        if(typeof options === 'undefined'){
            this.request = null;
        } else {
            this.request = options.request;
        }
    },
    model: Mail,
    sort_dir: "asc",
    timelineoptions: {
        showCurrentTime: true,
        zoomable: true,
        zoomMin: 1000 * 60 * 60 * 24,  // one day in milliseconds
        zoomMax: 1000 * 60 * 60 * 24 * 31,  // about one month in milliseconds
        //max: function () {
        //    var maxDate = new Date();
        //    maxDate.setDate(maxDate.getDate() + 7);
        //    return maxDate;
        //},
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
        template: _.template( $("#mail-plot").html()),
        orientation: {
        axis: "top",
        item: "top"
        },
        minHeight:'250px',
        //groupOrder: function (a, b) {
        //  return a.value - b.value;
        //},
        //
        order: function customOrder(a,b) {
            return a.ordinal - b.ordinal;
        }
    },

    localStorage: new Backbone.LocalStorage("messageList"),

    unread: function() {
        return _(this.filter( function(mail) { return !mail.get('read');} ) );
    },

    inbox: function(){
        return _(this.filter( function(mail) { return !mail.get('archived');}));
    },

    starred: function(){
        return _(this.filter( function(mail) { return mail.get('star');}));
    },

    unread_count: function() {
        return (this.filter ( function(mail) { return !mail.get('read');})).length;
    },

    labelled:function(label){
        return _(this.filter( function(mail) { return label in mail.get('label') } ));
    },

    starcount: function(){
        return (this.filter( function(mail) { return mail.get('star')})).length;
    },

    addOrdinal: function(numberofMessages){
        var counter = numberofMessages;
        this.each(function(item){
            item.setOrdinal(counter++);
            item.save()
        }, this);
    },

    getThreads: function (threadArray) {
        $('#visualization').html("");
        $('.inboxfunctions').addClass("hidden");
        $('.gridfunctions').removeClass("hidden");
        this.sort_dir = "desc";
        this.timeline = new vis.Timeline(document.getElementById('visualization'));
        this.groupDataSet = new vis.DataSet();
        this.itemDataSet = new vis.DataSet();
        this.groupCount = threadArray.length;
        this.groupCounter = 0;
        window.self = this;
        threadArray.forEach(function (threadid) {
            var request = $.ajax({
                url: "/threadslist",
                method: "POST",
                data: { "threadid" : threadid },
                dataType: "json"
            });
            request.done(function( response ) {
                self.renderMessages(response['currentMessageList']);
            });
            request.fail(function( jqXHR, textStatus ) {
                alert( "Request failed: " + textStatus );
            });
        });
    },

    /**
     * @param {{length:string}} currentMessageList
     * @param {{forEach:function}} currentMessageList
    **/
    renderMessages: function(currentMessageList){
        var messagesList = new MailList;
        messagesList.itemcount = currentMessageList.length;
        currentMessageList.forEach(function (message){
            self.renderMessageRow(message, messagesList);
        });
    },


    /**
     * @param {{sender:string}} message
     * @param {{subject:string}} message
     * @param {{snippet:string}} message
     * @param {{ordinal:string}} message
     * @param {{body:string}} message
     * @param {{date:string}} message
     * @param {{id:string}} message
     * @param messagesList
    **/
    renderMessageRow: function (message, messagesList){
        var start = message.date;
        var mailitem = new Mail({
            id: message.id,
            group: self.groupCounter,
            sender: message.sender,
            subject:message.subject,
            ordinal:message.ordinal,
            snippet:message.snippet + "...",
            mailbody:window.self.getBody(message.body),
            formattedDate:message.date,
            timestamp:message.date,
            start:start
        });
        messagesList.add(mailitem);
        mailitem.save();
        if (messagesList.itemcount==messagesList.length){
            self.groupDataSet.add({id: self.groupCounter, value: messagesList.models[0].get('timestamp'), content: "<span class='myGroup' style='color:#97B0F8; max-width:200px; white-space:wrap'>"+self.truncateTitle(messagesList.models[0].get('subject'))+"</span>"});
            self.itemDataSet.add(messagesList.toJSON());
            messagesList.reset();
            self.groupCounter+=1;
            if (self.groupCounter == self.groupCount){
                self.timeline.setOptions(self.timelineoptions);
                self.timeline.setGroups(self.groupDataSet);
                self.timeline.setItems(self.itemDataSet);
                $('body').append('<div id="overlay"></div>');
            }
        }
    },

    /**
     * @param {{parts:string}} message
     * @param {{body:string}} message
    **/
    getBody: function (message) {
        var encodedBody = '';
        if(typeof message.parts === 'undefined'){
          encodedBody = message.body;
        }else{
          encodedBody = window.self.getHTMLPart(message.parts);
        }
        encodedBody = encodedBody.replace(/-/g, '+').replace(/_/g, '/').replace(/\s/g, '');
        return decodeURIComponent(escape(window.atob(encodedBody)));
    },

    /**
     * @param {{length:array}} arr
    **/
    getHTMLPart: function(arr) {
        for(var x = 0; x <= arr.length; x++){
            if(typeof arr[x].parts === 'undefined'){
                if(arr[x].mimeType === 'text/html'){
                    return arr[x].body.data;
                }
            }else{
                return window.self.getHTMLPart(arr[x].parts);
            }
        }
        return '';
    },

    truncateTitle: function(title) {
        var length = 25;
        if (title.length > length) {
           title = title.substring(0, length)+'...';
        }
        return title;
    },

    search: function(word){
        if (word=="") return this;

        var pat = new RegExp(word, 'gi');
        return _(this.filter(function(mail) { 
            return pat.test(mail.get('subject')) || pat.test(mail.get('sender')); }));
    },

    comparator: function(mail){
        if (this.sort_dir === "desc"){
            return mail.get('timestamp');
        } else {
            return -mail.get('timestamp');
        }
    }
});

var InboxView = Backbone.View.extend({
    template: _.template($("#summary-tmpl").html()),
    emailreplytemplate: _.template($("#emailreply-template").html()),

    el: $("#mailapp"),

    initialize: function(){
        this.collection.bind('change', this.renderSideMenu, this);
        //this.render(this.collection);
        this.renderSideMenu();
    },

    events: {
        "click #fit": "fitall",
        "click #moveTo": "moveto",
        "click #visualization": "handleTimelineEvents",
        "click #window1": "setwindow",
        "click #previousweek": "previousweek",
        "change #labeler": "applyLabel",
        "click #markallread": "markallread",
        "click #archive": "archive",
        "click #gridview": "gridview",
        "click #allmail": "allmail",
        "click #inbox": "inbox",
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

    render: function(records){
        $('div#mail-list', this.el).html('');
        var self = this;
        records.each(function(item){
            self.addOne(item);
        }, this);
    },

    renderSideMenu: function(){
        $("#sidemenu").html( this.template(
            {'inbox': this.collection.unread_count(), 
             'starred':this.collection.starcount()}));
    },

    addOne: function (mail) {
        var itemView = new MailView({ model: mail});
        $('div#mail-list', this.el).append(itemView.render().el);
    },

    gridview: function(){
        var threadArray = [];
        this.collection.each(function(item){
            if(item.get('selected') == true){
              threadArray.push(item.get('id'));
            }
        }, this);
        this.collection.getThreads(threadArray);
    },

    fitall: function(){
        this.collection.timeline.fit();
    },

    moveto: function(){
        this.collection.timeline.moveTo('2015-10-14');
    },

    setwindow: function(){
        var today = new Date();
        var numberOfDaysToAdd = 2;
        var limitdate = today.setDate(today.getDate() + numberOfDaysToAdd); 
        var lastWeek = new Date(today.getTime()-1000*60*60*24*7);
        this.collection.timeline.setWindow(lastWeek, limitdate);
    },

    previousweek: function(){
        if(typeof begindate === 'undefined'){
            var begindate = new Date();
        } else {
            var begindate = previous;
        }
        var previous = new Date(begindate.getTime()-1000*60*60*24*7);
        var previous2 = new Date(previous.getTime()-1000*60*60*24*7);
        this.collection.timeline.setWindow(previous2, previous)
    },

    handleTimelineEvents: function(event) {
        if (typeof this.collection.timeline === 'undefined') {
            console.log("Timeline not yet defined..");
        } else {
            var props = this.collection.timeline.getEventProperties(event);
            if (typeof(props.item) === 'undefined' || props.item === null) {
                if(props.event.target.id == "emailreplyclose"){
                    $('#emailreply, #emailreplyclose, #overlay').fadeOut(300);
                } else {
                    console.log('no props item')
                }

            } else {
                this.renderemailbody(props);
            }
        }
    },

    renderemailbody: function(props){
        var currentid = props.item;
        var emailbody =  this.emailreplytemplate({'id': currentid});
        var overlay = document.getElementById('overlay');
        overlay.style.opacity = .7;
        $('#visualization').append(emailbody);
        $('#overlay, #emailreply').fadeIn(300);
    },

    attachToView: function(){
        this.el = $("#mail-list");
        var self = this;
        $(".mail").each(function(){
            var mailEl = $(this);
            var id = mailEl.data('threadid');
            var mailitem = self.collection.get(id);
            new MailView({
                model: mailitem,
                el: mailEl
            });
        });
    }
});

startapp = function () {
    window.threadslist = new MailList();
    $('.mail').each(function(i) {
        threadslist.add(new Mail({
            id: $(this).data('threadid'),
            ordinal: i,
            sender: this.getElementsByClassName("sender")[0].innerHTML,
            subject: this.getElementsByClassName("mail-subject")[0].innerHTML,
            snippet: this.getElementsByClassName("mail-snippet")[0].innerHTML,
            timestamp: this.getElementsByClassName("timestamp")[0].innerHTML,
            mailbody: '',
            start: '',
            read: false,
            star: false,
            selected:false,
            archived:false,
            label: '',
            createdOn: "Note created on " + new Date().toISOString()}
        ));
    }).promise().done( function(){
        window.currentInbox = new InboxView({collection: window.threadslist});
        window.currentInbox.attachToView();
        window.currentInbox.renderSideMenu()
    });
};

hover = function() {
    if (!document.body.currentStyle) return;
    var DIVbodywrapper = document.getElementsByClassName('bodywrapper');
    var DIVfullbody_wrap = document.getElementById('fullbody-wrap');
    DIVbodywrapper.onmouseover = function() {
        DIVfullbody_wrap.style.display = 'block';
    };
    DIVbodywrapper.onmouseout = function() {
        DIVfullbody_wrap.style.display = 'none';
    };
};

$( document ).ready(function() {
    startapp();
    hover();

});