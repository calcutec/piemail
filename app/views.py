import httplib2
import os
import datetime
from flask import url_for, session, redirect, request, json, render_template
from apiclient import discovery, errors, http
from oauth2client import client
from app import app

fullthreadset = []


@app.route('/')
def index():
    newthreadlist = []
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http_auth)
        # labels = listlabels(service, 'me')
        results = service.users().threads().list(userId='me',
                                                 maxResults=20,fields="threads/id",
                                                 q="in:inbox -category:(promotions OR social)").execute()
        batch = service.new_batch_http_request(callback=processthreads)
        for thread in results['threads']:
            batch.add(service.users()
                      .threads().get(userId='me', id=thread['id'],
                                     fields="messages/snippet, messages/internalDate, "
                                            "messages/threadId, messages/payload/headers"))
        batch.execute()
        for thread in fullthreadset:
            threaditems = dict()
            threaditems['threadId'] = thread['threadId']
            threaditems['snippet'] = thread['snippet'] + "..."
            threaditems['date'] = datetime.datetime.fromtimestamp(float(thread['internalDate'])/1000.).strftime("%Y-%m-%d %H:%M:%S")
            threaditems['sender'] = getheaders(thread, "From")
            threaditems['subject'] = getheaders(thread, "Subject")
            newthreadlist.append(threaditems)
        fullthreadset[:] = []
        return render_template("piemail.html", threads=newthreadlist, inbox=len(newthreadlist))


def processthreads(request_id, response, exception):
    if exception is not None:
        pass
    else:
        fullthreadset.append(response['messages'][0])


def getheaders(thread, key):
    for header in thread['payload']['headers']:
        if header['name'] == key:
            return header['value']


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


def listlabels(service, user_id):
    try:
        response = service.users().labels().list(userId=user_id).execute()
        labels = response['labels']
        for label in labels:
            print 'Label id: %s - Label name: %s' % (label['id'], label['name'])
            return labels
    except errors.HttpError, error:
        print 'An error occurred: %s' % error


def listthreadswithlabels(service, user_id, label_ids=[]):
    """List all Threads of the user's mailbox with label_ids applied.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Threads with these labelIds applied.

    Returns:
    List of threads that match the criteria of the query. Note that the returned
    list contains Thread IDs, you must use get with the appropriate
    ID to get the details for a Thread.
    """
    try:
        response = service.users().threads().list(userId=user_id, labelIds=label_ids, maxResults="100").execute()
        threads = []
        if 'threads' in response:
            threads.extend(response['threads'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().threads().list(userId=user_id, labelIds=label_ids,
                                                      pageToken=page_token).execute()
            threads.extend(response['threads'])
        return threads

    except errors.HttpError, error:
        print 'An error occurred: %s' % error


@app.route('/getmail')
def getmail():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        gmail_service = discovery.build('gmail', 'v1', http_auth)
        query = 'is:inbox'
        """List all Messages of the user's mailbox matching the query.

        Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        query: String used to filter messages returned.
        Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

        Returns:
        List of Messages that match the criteria of the query. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate ID to get the details of a Message.
        """
        try:
            response = gmail_service.users().messages().list(userId='me', q=query).execute()
            messages = []
            if 'messages' in response:
                print 'test %s' % response
                messages.extend(response['messages'])
            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = gmail_service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
                messages.extend(response['messages'])

            return json.jsonify({'data': messages})
        except errors.HttpError, error:
            print 'An error occurred: %s' % error


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


@app.route('/emaildata/<emailid>')
def emaildata(emailid):
    return render_template('emaildata.html', emailid=emailid)


@app.route('/getkey', methods=['POST'])
def getkey():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:

        token = credentials.access_token
        return json.dumps({"token": token})


# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html', error=error), 404
#
#
# @app.errorhandler(500)
# def internal_error(error):
#     return render_template('500.html', error=error), 500
