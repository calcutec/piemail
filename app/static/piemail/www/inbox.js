window.gapi = gapi;
window.gapi.client = gapi.client;
window.gapi.client.gmail = gapi.client.gmail;
window.gapi.client.gmail.users = gapi.client.gmail.users;
window.gapi.client.gmail.users.threads = gapi.client.gmail.users.threads;
window.gapi.client.gmail.users.messages = gapi.client.gmail.users.messages;

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
    },

    setOrdinal: function(ordinal){
        this.save( { ordinal: ordinal } );
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
        max: function () {
            var maxDate = new Date();
            maxDate.setDate(maxDate.getDate() + 7);
            return maxDate;
        },
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
        groupOrder: function (a, b) {
          return a.value - b.value;
        },

        order: function customOrder(a,b) {
            return a.timestamp - b.timestamp;
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
            item.setOrdinal(counter--);
            item.save()
        }, this);
    },

    getThreads: function (threadArray) {
        $('#visualization').innerHTML = "";
        $('.inboxfunctions').addClass("hidden");
        $('.gridfunctions').removeClass("hidden");
        this.sort_dir = "desc";
        this.timeline = new vis.Timeline(document.getElementById('visualization'));
        this.groupDataSet = new vis.DataSet();
        this.itemDataSet = new vis.DataSet();
        this.groupCount = threadArray.length;
        this.groupCounter = 0;  
        window.self = this;
        threadArray.forEach(
            function (threadIdentifier){
            var token = getSessionToken();
            console.log(token);
            gapi.client.gmail.users.threads.get({'userId': 'me','id': threadIdentifier}).then(function(resp){
                self.getMessages(resp.result);
            }
        );
        });
    },

    getMessages: function(response){
        var messagesList = new MailList;
        messagesList.itemcount = response.messages.length;
        response.messages.forEach(function (message){
            gapi.client.gmail.users.messages.get({'userId': 'me', 'id': message.id}).then(function(resp){
                self.renderMessageRow(resp.result, messagesList);
            });
        });
    },


    /**
     * @param {{payload:string}} message
     * @param {{id:string}} message
     * @param {{snippet:string}} message
     * @param messagesList
    **/
    renderMessageRow: function (message, messagesList){
        var start = new Date(getHeader(message.payload.headers, 'Date'));
        var mailitem = new Mail({
            id: message.id,
            group: self.groupCounter,
            sender:getHeader(message.payload.headers, 'From'),
            subject:getHeader(message.payload.headers, 'Subject'),
            content:getHeader(message.payload.headers, 'Subject'),
            snippet:message.snippet + "...",
            mailbody:getBody(message),
            formattedDate:new Date(getHeader(message.payload.headers, 'Date')).toLocaleString(), //Options do not work with Safari
            //formattedDate:formatDate(getHeader(message.payload.headers, 'Date')),
            timestamp:new Date(getHeader(message.payload.headers, 'Date')).getTime(),
            start:start
        });
        messagesList.add(mailitem);
        mailitem.save();
        if (messagesList.itemcount==messagesList.length){
            messagesList.addOrdinal(messagesList.length);
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
        this.listenTo(this.model, 'destroy', this.remove, this.unrender())
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

function getHeader(headers, index) {
    var header = '';
    $.each(headers, function(){
         if(this.name === index){
             header = this.value;
         }
    });
    return header;
}

/**
 * @param {{payload:string}} message
**/
function getBody(message) {
    var encodedBody = '';
    if(typeof message.payload.parts === 'undefined'){
      encodedBody = message.payload.body.data;
    }else{
      encodedBody = getHTMLPart(message.payload.parts);
    }
    encodedBody = encodedBody.replace(/-/g, '+').replace(/_/g, '/').replace(/\s/g, '');
    return decodeURIComponent(escape(window.atob(encodedBody)));
}

function getHTMLPart(arr) {
    for(var x = 0; x <= arr.length; x++){
        if(typeof arr[x].parts === 'undefined'){
            if(arr[x].mimeType === 'text/html'){
                return arr[x].body.data;
            }
        }else{
            return getHTMLPart(arr[x].parts);
        }
    }
    return '';
}

hover = function() {
    if (!document.body.currentStyle) return;
    var DIVmailwrapper = document.getElementsByClassName('mailwrapper');
    var DIVcomment_wrap = document.getElementById('comment-wrap');
    DIVmailwrapper.onmouseover = function() {
        DIVcomment_wrap.style.display = 'block';
    };
    DIVmailwrapper.onmouseout = function() {
        DIVcomment_wrap.style.display = 'none';
    };
};


startapp = function () {
    var threadslist = new MailList();
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
        var currentInbox = new InboxView({collection: threadslist});
        currentInbox.attachToView();
        currentInbox.renderSideMenu()
    });
};

function getSessionToken() {
    $.ajax({
        type: 'POST',
        url: 'http://localhost:8000/getkey',
        /**
         * @param {{iserror:string}} response
         * @param {{savedsuccess:string}} response
         * @param {{token:string}} response
        **/
        success: function(response) {
            if(response.iserror) {
                console.log('pass not found')
            }else if (response.savedsuccess) {
                console.log('token received');
                return response.token;
            }
        },
        error: function() {
            console.log('there was a problem getting the token');
        }
    });

}


$( document ).ready(function() {
    startapp();
    hover();
});


