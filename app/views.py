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
from app import cache

from datetime import timedelta
from flask import make_response, current_app
from functools import update_wrapper

compiler = Compiler()

fullmessageset = []
parsedmessageset = []


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/')
def index():
    basedir = os.path.abspath(os.path.dirname(__file__))
    templatedir = os.path.join(basedir, 'static/piemail/www/libs/templates/email-list.handlebars')
    source = open(templatedir, "r").read().decode('utf-8')
    return render_template("testtemplate.html")

    # template = compiler.compile(source)
    # if 'credentials' not in session:
    #     return redirect(url_for('oauth2callback'))
    # credentials = client.OAuth2Credentials.from_json(session['credentials'])
    # if credentials.access_token_expired:
    #     return redirect(url_for('oauth2callback'))
    # else:
    #     http_auth = credentials.authorize(httplib2.Http())
    #
    # service = discovery.build('gmail', 'v1', http=http_auth)
    # results = service.users().threads().list(userId='me', maxResults=50, fields="threads/id", q="in:inbox").execute()
    #
    # batch = service.new_batch_http_request(callback=processthreads)
    # for thread in results['threads']:
    #     batch.add(service.users().threads().get(userId='me', id=thread['id']))
    #     # batch.add(service.users().threads().get(userId='me', id=thread['id'],
    #     #                                 fields="messages/snippet, messages/internalDate, messages/labelIds, "
    #     #                                        "messages/threadId, messages/payload/headers"))
    # batch.execute()
    # for emailthread in fullmessageset:
    #     # t = threading.Thread(target=parse_thread, kwargs={"emailthread": emailthread})
    #     # t.start()
    #     parse_thread(emailthread)
    # newcollection = deepcopy(parsedmessageset)
    # fullmessageset[:] = []
    # parsedmessageset[:] = []
    # context = newcollection
    # output = template(context)
    # cache.set(credentials.access_token, newcollection, 15)
    # return render_template("piemail.html", output=output)


@app.route('/inbox', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def inbox():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    cachedcollection = cache.get(credentials.access_token)
    return json.dumps({'newcollection': cachedcollection})


@app.route('/signmeout', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def signmeout():
    if request.is_xhr:
        return json.dumps({'status': 'OK', 'redirect_url': '/signmeout'})
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    credentials.revoke(httplib2.Http())
    session.clear()
    return render_template("login.html")


@app.route('/threadslist', methods=['POST', 'GET', 'OPTIONS'])
@crossdomain(origin='*')
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


def processthreads(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullmessageset.append((request_id, response['messages'][0]))


def processmessages(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullmessageset.append((request_id, response))


@app.route('/emaildata/<emailid>', methods=['POST', 'GET', 'OPTIONS'])
@crossdomain(origin='*')
def emaildata(emailid):
    return render_template('emaildata.html', emailid=emailid)


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


def parse_thread(emailthread):
    threaditems = dict()
    # INBOX, CATEGORY_SOCIAL, CATEGORY_PERSONAL, CATEGORY_PROMOTIONS, CATEGORY_FORUMS, CATEGORY_UPDATES, SENT,
    # PURCHASES, TRAVEL, FINANCE, STARRED, UNREAD, INBOX, IMPORTANT
    threaditems['labels'] = emailthread[1]['labelIds']
    if 'UNREAD' in emailthread[1]['labelIds']:
        threaditems['unread'] = True
    else:
        threaditems['unread'] = False
    if 'STARRED' in emailthread[1]['labelIds']:
        threaditems['star'] = True
    else:
        threaditems['star'] = False
    if 'CATEGORY_PROMOTIONS' in emailthread[1]['labelIds']:
        threaditems['category'] = 'promotions'
    if 'CATEGORY_SOCIAL' in emailthread[1]['labelIds']:
        threaditems['category'] = 'social'
    if 'CATEGORY_UPDATES' in emailthread[1]['labelIds']:
        threaditems['category'] = 'updates'
    if 'CATEGORY_FORUMS' in emailthread[1]['labelIds']:
        threaditems['category'] = 'forums'
    if 'INBOX' in emailthread[1]['labelIds'] \
            and 'CATEGORY_SOCIAL' not in emailthread[1]['labelIds'] \
            and 'CATEGORY_PROMOTIONS' not in emailthread[1]['labelIds'] \
            and 'CATEGORY_UPDATES' not in emailthread[1]['labelIds'] \
            and 'CATEGORY_FORUMS' not in emailthread[1]['labelIds']:
        threaditems['category'] = 'primary'
    if 'SENT' in emailthread[1]['labelIds']:
        threaditems['category'] = 'sent'
    if 'INBOX' in emailthread[1]['labelIds']:
        threaditems['inbox'] = True
    else:
        threaditems['inbox'] = False
    threaditems['threadId'] = emailthread[1]['threadId']
    threaditems['id'] = emailthread[1]['threadId']
    threaditems['snippet'] = emailthread[1]['snippet'] + "..."
    threaditems['timestamp'] = datetime.datetime.fromtimestamp(float(emailthread[1]['internalDate'])/1000.)\
        .strftime("%I:%M %p %b %d")
    threaditems['sender'] = getheaders(emailthread[1], "From")
    threaditems['subject'] = getheaders(emailthread[1], "Subject")
    threaditems['ordinal'] = emailthread[0]
    threaditems['body'] = getbody(emailthread[1])
    threaditems['rawtimestamp'] = emailthread[1]['internalDate']
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


@app.route('/oauth2callback', methods=['POST', 'GET', 'OPTIONS'])
@crossdomain(origin='*')
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


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', error=error), 500

