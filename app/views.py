from app import app
from flask import render_template, request
import os


@app.route('/')
def index():
    return render_template('piemail.html')


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


