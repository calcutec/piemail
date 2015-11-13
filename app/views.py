import httplib2
import os
from flask import url_for, session, redirect, request, render_template, jsonify, json
from apiclient import discovery, errors
from oauth2client import client
from app import app
from copy import deepcopy
import threading
import datetime
import base64
import re
from pybars import Compiler

compiler = Compiler()
basedir = os.path.abspath(os.path.dirname(__file__))

fullmessageset = []
parsedmessageset = []


@app.route('/')
def index():
    source = open('/Users/bburton/piemail/app/static/piemail/www/libs/templates/test-server.handlebars', "r")\
        .read().decode('utf-8')

    template = compiler.compile(source)
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())

    service = discovery.build('gmail', 'v1', http=http_auth)
    results = service.users().threads().list(userId='me',
                                             maxResults=20, fields="threads/id",
                                             q="in:inbox -category:(promotions OR social)").execute()
    batch = service.new_batch_http_request(callback=processthreads)
    for thread in results['threads']:
        batch.add(service.users().threads().get(userId='me', id=thread['id'],
                                                fields="messages/snippet, messages/internalDate, messages/labelIds, "
                                                       "messages/threadId, messages/payload/headers"))
    batch.execute()
    for emailthread in fullmessageset:
        t = threading.Thread(target=parse_thread, kwargs={"emailthread": emailthread})
        t.start()
    newcollection = deepcopy(parsedmessageset)
    fullmessageset[:] = []
    parsedmessageset[:] = []
    context = newcollection
    output = template(context)
    return render_template("piemail.html", output=output)


@app.route('/signmeout', methods=['GET', 'POST'])
def signmeout():
    if request.is_xhr:
        return json.dumps({'status': 'OK', 'redirect_url': '/signmeout'})
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    credentials.revoke(httplib2.Http())
    session.clear()
    return render_template("login.html")


@app.route('/inbox', methods=['GET', 'POST'])
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
                                             maxResults=50, fields="threads/id",
                                             q="in:inbox -category:(promotions OR social)").execute()
    batch = service.new_batch_http_request(callback=processthreads)
    for thread in results['threads']:
        batch.add(service.users().threads().get(userId='me', id=thread['id'],
                                                fields="messages/snippet, messages/internalDate, messages/labelIds, "
                                                       "messages/threadId, messages/payload/headers"))
    batch.execute()
    for emailthread in fullmessageset:
        t = threading.Thread(target=parse_thread, kwargs={"emailthread": emailthread})
        t.start()
    newcollection = deepcopy(parsedmessageset)
    fullmessageset[:] = []
    parsedmessageset[:] = []
    return json.dumps({'newcollection': newcollection})


def processthreads(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullmessageset.append((request_id, response['messages'][0]))


@app.route('/threadslist', methods=['POST', 'GET'])
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
        return jsonify(error)

    batch = service.new_batch_http_request(callback=processmessages)
    for message in thread['messages']:
        batch.add(service.users().messages().get(userId='me', id=message['id']))
    batch.execute()
    for emailmessage in fullmessageset:
        m = threading.Thread(target=parse_message, kwargs={"emailmessage": emailmessage})
        m.start()
    response = dict()
    response['iserror'] = False
    response['savedsuccess'] = True
    response['currentMessageList'] = deepcopy(parsedmessageset)
    fullmessageset[:] = []
    parsedmessageset[:] = []
    return jsonify(response)


def processmessages(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullmessageset.append((request_id, response))


@app.route('/emaildata/<emailid>')
def emaildata(emailid):
    return render_template('emaildata.html', emailid=emailid)


@app.route('/oauth2callback')
def oauth2callback(final_url='index'):
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
        return redirect(url_for(final_url))


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


def parse_thread(emailthread):
    threaditems = dict()
    threaditems['labels'] = emailthread[1]['labelIds']
    if 'UNREAD' in emailthread[1]['labelIds']:
        threaditems['unread'] = True
    else:
        threaditems['unread'] = False
    if 'PROMOTIONS' in emailthread[1]['labelIds']:
        threaditems['promotions'] = True
    else:
        threaditems['promotions'] = False
    threaditems['threadId'] = emailthread[1]['threadId']
    threaditems['id'] = emailthread[1]['threadId']
    threaditems['snippet'] = emailthread[1]['snippet'] + "..."
    threaditems['timestamp'] = datetime.datetime.fromtimestamp(float(emailthread[1]['internalDate'])/1000.)\
        .strftime("%I:%M %p %b %d")
    threaditems['sender'] = getheaders(emailthread[1], "From")
    threaditems['subject'] = getheaders(emailthread[1], "Subject")
    parsedmessageset.append(threaditems)


def parse_message(emailmessage):
    messageitems = dict()
    messageitems['id'] = emailmessage[1]['id']
    messageitems['threadId'] = emailmessage[1]['threadId']
    messageitems['snippet'] = emailmessage[1]['snippet']
    messageitems['timestamp'] = datetime.datetime.fromtimestamp(float(emailmessage[1]['internalDate'])/1000.)\
        .strftime("%H:%M:%S %Y-%m-%d ")
    messageitems['sender'] = getheaders(emailmessage[1], "From")
    messageitems['subject'] = getheaders(emailmessage[1], "Subject")
    messageitems['body'] = getbody(emailmessage[1])
    messageitems['ordinal'] = emailmessage[0]
    parsedmessageset.append(messageitems)


def getheaders(emailthread, key):
    for header in emailthread['payload']['headers']:
        if header['name'] == key:
            return header['value']


def getbody(message):
    if 'parts' in message['payload']:
        encodedbody = gethtmlpart(message['payload']['parts'])
    else:
        encodedbody = message['payload']['body']['data']
    decodedbody = base64.urlsafe_b64decode(str(encodedbody))
    decodedbody = \
        re.sub(r'src="cid:([^"]+)"', "src='/static/piemail/www/icons/no_image_available.svg'", decodedbody)  # cid hack
    return decodedbody


def gethtmlpart(parts):
    for part in parts:
        if 'parts' not in part:
            if part['mimeType'] == 'text/html':
                return part['body']['data']
        else:
            return gethtmlpart(part['parts'])
    return ''
