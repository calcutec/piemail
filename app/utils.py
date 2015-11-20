import os
import threading
from datetime import timedelta
from flask import make_response, current_app, request, render_template, jsonify
from apiclient import discovery, errors
from functools import update_wrapper
from app import app
from copy import deepcopy
from app import cache
from pybars import Compiler
import datetime
import base64
import re

compiler = Compiler()
fullmessageset = []
parsedmessageset = []


def getcachedthreads():
    newcollection = None
    cachedmessagesetids = cache.get('cachedmessagesetids')
    if cachedmessagesetids:
        for emailthreadid in cachedmessagesetids:
            cachedthread = cache.get(emailthreadid['id'])
            if cachedthread:
                parsedmessageset.append(cachedthread)
        newcollection = deepcopy(parsedmessageset)
        parsedmessageset[:] = []
    return newcollection


def rendercollection(newcollection):
    basedir = os.path.abspath(os.path.dirname(__file__))
    templatedir = os.path.join(basedir, 'static/piemail/www/libs/templates/email-list.handlebars')
    source = open(templatedir, "r").read().decode('utf-8')
    template = compiler.compile(source)
    output = template(newcollection)
    return output


def getcontext(http_auth=None, retrievebody=None):
    service = discovery.build('gmail', 'v1', http=http_auth)
    results = service.users().threads().list(userId='me', maxResults=20, fields="threads/id", q="in:inbox").execute()
    batch = service.new_batch_http_request(callback=processthreads)
    cache.set('cachedmessagesetids', results['threads'], timeout=300)  # Cache for 5 minutes
    for thread in results['threads']:
        # batch.add(service.users().threads().get(userId='me', id=thread['id']))
        batch.add(service.users().threads().get(userId='me', id=thread['id'], fields="messages/snippet, "
                                                                                     "messages/internalDate, "
                                                                                     "messages/labelIds, "
                                                                                     "messages/threadId, "
                                                                                     "messages/payload/parts, "
                                                                                     "messages/payload/body, "
                                                                                     "messages/payload/headers"))
    batch.execute()
    for item in fullmessageset:
        # t = threading.Thread(target=parse_thread, kwargs={"item": item})
        # t.start()
        parse_item(item, retrievebody)
    newcollection = deepcopy(parsedmessageset)
    fullmessageset[:] = []
    parsedmessageset[:] = []
    return newcollection


def getresponse(http_auth):
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
    for item in fullmessageset:
        # m = threading.Thread(target=parse_item, kwargs={"item": item, "retrievebody": True})
        # m.start()
        parse_item(item, retrievebody=True)
    response = dict()
    response['iserror'] = False
    response['savedsuccess'] = True
    response['currentMessageList'] = deepcopy(parsedmessageset)
    fullmessageset[:] = []
    parsedmessageset[:] = []
    return response


def processthreads(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullmessageset.append((request_id, response['messages'][-1], len(response['messages'])))


def processmessages(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullmessageset.append((request_id, response))


def parse_item(item, retrievebody=False):
    threaditems = dict()
    # INBOX, CATEGORY_SOCIAL, CATEGORY_PERSONAL, CATEGORY_PROMOTIONS, CATEGORY_FORUMS, CATEGORY_UPDATES, SENT,
    # PURCHASES, TRAVEL, FINANCE, STARRED, UNREAD, INBOX, IMPORTANT
    threaditems['labels'] = item[1]['labelIds']
    if 'UNREAD' in item[1]['labelIds']:
        threaditems['unread'] = True
    else:
        threaditems['unread'] = False
    if 'STARRED' in item[1]['labelIds']:
        threaditems['star'] = True
    else:
        threaditems['star'] = False
    if 'CATEGORY_PROMOTIONS' in item[1]['labelIds']:
        threaditems['category'] = 'promotions'
    if 'CATEGORY_SOCIAL' in item[1]['labelIds']:
        threaditems['category'] = 'social'
    # if 'CATEGORY_UPDATES' in item[1]['labelIds']:
    #     threaditems['category'] = 'updates'
    # if 'CATEGORY_FORUMS' in item[1]['labelIds']:
    #     threaditems['category'] = 'forums'
    if 'CATEGORY_SOCIAL' not in item[1]['labelIds'] and 'CATEGORY_PROMOTIONS' not in item[1]['labelIds']:
            # and 'CATEGORY_UPDATES' not in item[1]['labelIds'] \
            # and 'CATEGORY_FORUMS' not in item[1]['labelIds']:
        threaditems['category'] = 'primary'
    if 'INBOX' in item[1]['labelIds']:
        threaditems['inbox'] = True
    else:
        threaditems['inbox'] = False
    if 'INBOX' not in item[1]['labelIds'] and 'SENT' in item[1]['labelIds']:
        threaditems['category'] = 'sent'
    threaditems['threadId'] = item[1]['threadId']
    threaditems['id'] = item[1]['threadId']
    threaditems['snippet'] = item[1]['snippet'] + "..."
    threaditems['timestamp'] = datetime.datetime.fromtimestamp(float(item[1]['internalDate'])/1000.)\
        .strftime("%I:%M %p %b %d")
    threaditems['sender'] = getheaders(item[1], "From")
    if threaditems['sender'] == getheaders(item[1], "To"):
        threaditems['sender'] = "Me"
    threaditems['receiveddate'] = getheaders(item[1], "Date")
    threaditems['subject'] = getheaders(item[1], "Subject")
    if retrievebody:
        threaditems['body'] = getbody(item[1])
    threaditems['rawtimestamp'] = item[1]['internalDate']
    threaditems['ordinal'] = item[0]
    if len(item) > 2:  # Threads with multiple messages
        threaditems['length'] = item[2]
    cache.set(threaditems['id'], threaditems, timeout=300)  # Cache for 5 minutes
    parsedmessageset.append(threaditems)


def getheaders(item, key):
    for header in item['payload']['headers']:
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


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', error=error), 500
