    function log(mess) {
        $('#logs').prepend('<pre>' + mess + '</pre>');
        console.log(mess);
    }
  
    function logJSON(mess, json) {
        log(mess + JSON.stringify(json, null, 2));
    }
  
    function saveTokens(tokens) {
        localStorage['gapi_tokens'] = JSON.stringify(tokens);
    }

    var clientId = '1019317791133-t3jpuu40sn9t7s2ll7gde70phppoq7b1.apps.googleusercontent.com';
    var apiKey = 'OMfRw_hfmWTUSLwXK-3aQSjg';
    var scopes = 'https://www.googleapis.com/auth/gmail.readonly';

    function handleClientLoad() {
        gapi.client.setApiKey(apiKey);
        window.setTimeout(checkAuth, 1);
    }

    function checkAuth() {
        gapi.auth.authorize({
            client_id: clientId,
            scope: scopes,
            immediate: true
        }, handleAuthResult);
    }

    function handleAuthClick() {
        gapi.auth.authorize({
            client_id: clientId,
            scope: scopes,
            immediate: false
        }, handleAuthResult);
        return false;
    }

    function handleAuthResult(authResult) {
        if(authResult && !authResult.error) {
            loadGmailApi();
            $('#authorize-button').remove();
            $('#mailapp').removeClass("hidden");
            $('.inboxfunctions').removeClass("hidden")
        } else {
            $('#authorize-button').removeClass("hidden");
            $('#authorize-button').on('click', function(){
                handleAuthClick();
            });
        }
    }

    function loadCollection(){
        alert('collection loaded!')
    }

    function loadGmailApi() {
        gapi.client.setApiKey(""); 
        gapi.client.load('gmail', 'v1', displayInbox);
    }