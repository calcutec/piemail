import httplib2
from flask import url_for, session, redirect, request, render_template, jsonify, json
from oauth2client import client
from app import app
from utils import crossdomain, getcachedthreads, rendercollection, getcontext, getmessages
from app import cache


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('inbox'))


@app.route('/inbox', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def inbox():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    http_auth = credentials.authorize(httplib2.Http())

    # newcollection = getcachedthreads()
    # if newcollection:
    #     output = rendercollection(newcollection)
    #     return render_template("piemail.html", output=output, data=json.dumps(newcollection))
    # else:
    newcollection = getcontext(http_auth, retrievebody=False)
    output = rendercollection(newcollection)
    return render_template("piemail.html", output=output, data=json.dumps(newcollection))


# @app.route('/mailbody', methods=['POST', 'GET', 'OPTIONS'])
# @crossdomain(origin='*')
# def mailbody():
#     if 'credentials' not in session:
#         return redirect(url_for('oauth2callback'))
#     credentials = client.OAuth2Credentials.from_json(session['credentials'])
#     if credentials.access_token_expired:
#         return redirect(url_for('oauth2callback'))
#     else:
#         http_auth = credentials.authorize(httplib2.Http())
#     context = getcontext(http_auth, retrievebody=True)
#     response = dict()
#     response['iserror'] = False
#     response['savedsuccess'] = True
#     response['currentMessageList'] = context
#     return jsonify(response)


# @app.route('/threadslist', methods=['POST', 'GET', 'OPTIONS'])
# @crossdomain(origin='*')
# def threadslist():
#     if 'credentials' not in session:
#         return redirect(url_for('oauth2callback'))
#     credentials = client.OAuth2Credentials.from_json(session['credentials'])
#     if credentials.access_token_expired:
#         return redirect(url_for('oauth2callback'))
#     else:
#         http_auth = credentials.authorize(httplib2.Http())
#     response = getresponse(http_auth)
#     return jsonify(response)


# @app.route('/emaildata/<emailid>', methods=['POST', 'GET', 'OPTIONS'])
# @crossdomain(origin='*')
# def emaildata(emailid):
#     return render_template('emaildata.html', emailid=emailid)


@app.route('/api/threads/<threadid>/messages', methods=['POST', 'GET', 'OPTIONS'])
@crossdomain(origin='*')
def messages(threadid):
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
    response = getmessages(http_auth, threadid)
    response = response['currentmessagelist']
    return json.dumps(response)


@app.route('/oauth2callback', methods=['POST', 'GET', 'OPTIONS'])
@crossdomain(origin='*')
def oauth2callback(final_url='inbox'):
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


@app.route('/signmeout', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def signmeout():
    if request.is_xhr:
        return json.dumps({'status': 'OK', 'redirect_url': '/signmeout'})
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    credentials.revoke(httplib2.Http())
    session.clear()
    return render_template("login.html")
