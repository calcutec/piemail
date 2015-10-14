var Mail = Backbone.Model.extend( {
    defaults: {
        gmailId: '',
        subject: '',
        snippet: '',
        body: '',
        read: false,
        star: false,
        selected:false,
        archived:false,
        label: ''
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

var MailList = Backbone.Collection.extend({
    model: Mail,

    localStorage: new Store("mails"),

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

    search: function(word){
        if (word=="") return this;

        var pat = new RegExp(word, 'gi');
        return _(this.filter(function(mail) { 
            return pat.test(mail.get('subject')) || pat.test(mail.get('sender')); }));
    },
    comparator: function(mail){
        return -mail.get('timestamp').getTime();
    }
});

var MailView = Backbone.View.extend({
    tagName: "div",
    className: "topcoat-grid__column--auto",

    template: _.template( $("#mail-item").html()),

    events: {
        // "click .mail-subject,.sender,.mail-snippet" : "markRead",
        "click .mail-subject,.sender,.mail-snippet" : "getMail",
        "click .star" : "star",
        "click .check" : "select"
    },

    initialize: function() {
        this.model.bind('change', this.render, this);
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
        this.model.markRead();
        getThread(this.model.get('gmailId'));
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

    el: $("#mailapp"),

    initialize: function(){

        this.collection.bind('change', this.renderSideMenu, this);
        this.render(this.collection);
        this.renderSideMenu();
    },

    events: {
        "change #labeler" : "applyLabel",
        "click #markallread" : "markallread",
        "click #archive" : "archive",
        "click #gridview" : "gridview",
        "click #allmail" : "allmail",
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

    gridview: function(){
        var gridviewlist = [];
        this.collection.each(function(item){
            if(item.get('selected') == true){
              gridviewlist.push(item.get('gmailId'));
            }
        }, this);
        getListOfThreads(gridviewlist);
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
    }
});


function log(mess) {
    $('#logs').prepend('<pre>' + mess + '</pre>');
    console.log(mess);
}

function logJSON(mess, json) {
    log(mess + JSON.stringify(json, null, 2));
}
 

 // Show list of threads
 function displayInbox() {
    var request = gapi.client.gmail.users.threads.list({
        'userId': 'me',
        'labelIds': 'INBOX',
        'maxResults': 15
    });
    list = new MailList();
    request.execute(function(response) {
        count = response.threads.length;
        $.each(response.threads, function() {
             var threadRequest = gapi.client.gmail.users.threads.get({
                  'userId': 'me',
                  'id': this.id
              });
             threadRequest.execute(appendThreadRow);
        });
    });
 }

// Show list of messages, not grouped by thread
//function displayInbox() {
//    var request = gapi.client.gmail.users.messages.list({
//        'userId': 'me',
//        'labelIds': 'INBOX',
//        'maxResults': 30
//    });
//    list = new MailList();
//    request.execute(function(response) {
//        count = response.messages.length;
//        $.each(response.messages, function() {
//             var messageRequest = gapi.client.gmail.users.messages.get({
//                  'userId': 'me',
//                  'id': this.id
//              });
//             messageRequest.execute(appendMessageRow);
//        });
//    });
//}

// Show messages for selected threads
function getListOfThreads(threadList) {
    list = new MailList();
    var arrayLength = threadList.length;
    for (var i = 0; i < arrayLength; i++) {
        getThread(threadList[i]);
    };
}

function getThread(threadId) {
     var request = gapi.client.gmail.users.threads.get({
         'userId': 'me',
         'id': threadId
     });
     request.execute(function(response) {
         // logJSON('response: ', response)
         count = response.messages.length;
         $.each(response.messages, function() {
              var messageRequest = gapi.client.gmail.users.messages.get({
                   'userId': 'me',
                   'id': this.id
               });
              messageRequest.execute(appendMessageRow);
         });
     });
 }

// Show message
function getMail(messageId) {
    var request = gapi.client.gmail.users.messages.get({
        'userId': 'me',
        'id': messageId
    });
    list = new MailList();
    request.execute(function(response) {
        count = 1;
        appendMessage(response);
    });
}

function appendMessage(message) {
    var mailitem = new Mail({
        gmailId: message.id,
        sender:getHeader(message.payload.headers, 'From'),
        subject:getHeader(message.payload.headers, 'Subject'),
        body: getBody(message),
        formattedDate:formatDate(getHeader(message.payload.headers, 'Date')),
        timestamp: new Date(getHeader(message.payload.headers, 'Date'))
    });

    list.add(mailitem);
    NewApp = new InboxView({collection:list});
}

function appendMessageRow(message) {
    //logJSON('message: ', message)
    var mailitem = new Mail({
        gmailId: message.id,
        sender:getHeader(message.payload.headers, 'From'),
        subject:getHeader(message.payload.headers, 'Subject'),
        snippet:message.snippet,
        formattedDate:formatDate(getHeader(message.payload.headers, 'Date')),
        timestamp:new Date(getHeader(message.payload.headers, 'Date'))
    });
    list.add(mailitem);
    if (count==list.length) NewApp = new InboxView({collection:list});
}

function appendThreadRow(thread) {
    var mailitem = new Mail({
        gmailId: thread.id,
        sender:getHeader(thread.messages[thread.messages.length-1].payload.headers, 'From'),
        subject:getHeader(thread.messages[thread.messages.length-1].payload.headers, 'Subject'),
        snippet:thread.messages[thread.messages.length-1].snippet,
        formattedDate:formatDate(getHeader(thread.messages[thread.messages.length-1].payload.headers, 'Date')),
        timestamp:new Date(getHeader(thread.messages[thread.messages.length-1].payload.headers, 'Date'))
    });

    list.add(mailitem);
    if (count==list.length) NewApp = new InboxView({collection:list});
}

function formatDate(dateToFormat) {
    var date = new Date(dateToFormat);

    var month = date.getMonth() + 1;
    var day = date.getDate();
    var hour = date.getHours();
    var min = date.getMinutes();
    var sec = date.getSeconds();

    month = (month < 10 ? "0" : "") + month;
    day = (day < 10 ? "0" : "") + day;
    hour = (hour < 10 ? "0" : "") + hour;
    min = (min < 10 ? "0" : "") + min;
    sec = (sec < 10 ? "0" : "") + sec;

    var str = date.getFullYear() + "-" + month + "-" + day + " at " +  hour + ":" + min;

    return str;
}

function getHeader(headers, index) {
    var header = '';
    $.each(headers, function(){
         if(this.name === index){
             header = this.value;
         }
    });
    return header;
}

function getBody(message) {
    var encodedBody = '';
    if(typeof message.payload.parts === 'undefined'){
      encodedBody = message.payload.body.data;
    }else{
      encodedBody = getHTMLPart(message.payload.parts);
    }
    encodedBody = encodedBody.replace(/-/g, '+').replace(/_/g, '/').replace(/\s/g, '');
    decodedBody = decodeURIComponent(escape(window.atob(encodedBody)));
    return decodedBody
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
