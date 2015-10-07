/*
 * Logging code
 */
function logClear() {
    $('#logs').html('');
}

function log(mess) {
    $('#logs').prepend('<pre>' + mess + '</pre>');
    console.log(mess);
}

function logJSON(mess, json) {
    log(mess + JSON.stringify(json, null, 2));
}

/*
 * Save tokens in localStorage so they will persist between runs
 */
function saveTokens(tokens) {
    localStorage['gapi_tokens'] = JSON.stringify(tokens);
}

function getTokens() {
    return JSON.parse(localStorage['gapi_tokens']);
}

/*
 * This is for "Other client 1" credential of netbard-auto-login
 *
 */
var params = {
    client_id: '1019317791133-o4lt8c9kar2sav1tmhks1pu2chrgab6u.apps.googleusercontent.com',
    client_secret: '0evxZad_gWe9uMU7snk_DVsf',
    scope: 'https://www.googleapis.com/auth/gmail.readonly',
    callback: function(error, tokens) {
        if (error) log('error: ' + error);
        else {
            saveTokens(tokens);
            logJSON('tokens: ', tokens);
        }
    }
};

function signInTest() {
    logClear();
    log('Sign in');
    phonegapi.signIn(params);
}

function refreshTest() {
    logClear();
    log('Refresh');
    phonegapi.refreshSignIn(getTokens(), params);
}

function signOutTest() {
    logClear();
    log('Sign out');
    phonegapi.signOut(function(tokens) {
        saveTokens(tokens);
    });
}

/*
 * Test if we are authenticated by listing inbox labels
 */
//function leaderboards() {
//    log('leaderboards');
//    gapi.client.request({
//        path: '/games/v1/leaderboards',
//        params: {maxResults: 5},
//        callback: function(response) {
//            logJSON('leaderboards: ', response);
//        }});
//}

function loadGmailApi() {
    gapi.client.load('gmail', 'v1', listLabels);
}

/**
 * Print all Labels in the authorized user's inbox. If no labels
 * are found an appropriate message is printed.
 */
function listLabels() {
    logClear();
    $('#output').html('');
    var request = gapi.client.gmail.users.labels.list({'userId': 'me'});
    request.execute(function(resp) {
        var labels = resp.labels;
        appendPre('Labels:');

        if (labels && labels.length > 0) {
            for (i = 0; i < labels.length; i++) {
                var label = labels[i];
                appendPre(label.name)
            }
        } else {
            appendPre('No Labels found.');
        }
    });
}

/**
 * Append a pre element to the body containing the given message
 * as its text node.
 *
 * @param {string} message Text to be placed in pre element.
 */
function appendPre(message) {
    var pre = document.getElementById('output');
    var textContent = document.createTextNode(message + '\n');
    pre.appendChild(textContent);
}
