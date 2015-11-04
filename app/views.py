import httplib2
import os
import functions
from flask import url_for, session, redirect, request, render_template, jsonify, json
from apiclient import discovery, errors
from oauth2client import client
from app import app
from copy import deepcopy

fullthreadset = []
fullmessageset = []


@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        return render_template("piemail.html")


@app.route('/inbox', methods=['GET'])
def inbox():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())

    service = discovery.build('gmail', 'v1', http=http_auth)
    results = service.users().threads().list(userId='me',
                                             maxResults=50,fields="threads/id",
                                             q="in:inbox -category:(promotions OR social)").execute()
    batch = service.new_batch_http_request(callback=processthreads)
    for thread in results['threads']:
        batch.add(service.users()
            .threads().get(userId='me', id=thread['id'],
            fields="messages/snippet, messages/internalDate, messages/labelIds, messages/threadId, messages/payload/headers"))
    batch.execute()
    newcollection = deepcopy(fullthreadset)
    fullmessageset[:] = []
    return json.dumps({'newcollection': newcollection})


def processthreads(request_id, response, exception):
    if exception is not None:
        pass
    else:
        emailthread = response['messages'][0]
        fullthreadset.append(functions.parse_thread(emailthread))


@app.route('/threadslist', methods=['POST'])
def threadslist():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())

    service = discovery.build('gmail', 'v1', http=http_auth)
    threadid = request.values['threadid']
    try:
        thread = service.users().threads().get(userId='me', id=threadid).execute()
    except errors.HttpError, error:
        print 'An error occurred: %s' % error

    batch = service.new_batch_http_request(callback=processmessages)
    for message in thread['messages']:
        batch.add(service.users().messages().get(userId='me', id=message['id']))
    batch.execute()
    response = dict()
    response['iserror']= False
    response['savedsuccess'] = True
    response['currentMessageList'] = deepcopy(fullmessageset)
    fullmessageset[:] = []
    return jsonify(response)


def processmessages(request_id, response, exception):
    if exception is not None:
        pass
    else:
        emailmessage = response
        fullmessageset.append(functions.parse_message(emailmessage))


@app.route('/emaildata/<emailid>')
def emaildata(emailid):
    return render_template('emaildata.html', emailid=emailid)


@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets(
        'client_secrets.json',
        scope='https://mail.google.com/',
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('index'))


@app.context_processor
def inject_static_url():
    local_static_url = app.static_url_path
    static_url = 'https://s3.amazonaws.com/netbardus/'
    if os.environ.get('HEROKU') is not None:
        local_static_url = static_url
    if not static_url.endswith('/'):
        static_url += '/'
    if not local_static_url.endswith('/'):
        local_static_url += '/'
    return dict(
        static_url=static_url,
        local_static_url=local_static_url,
        host_url=request.url_root
    )


# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html', error=error), 404
#
#
# @app.errorhandler(500)
# def internal_error(error):
#     return render_template('500.html', error=error), 500