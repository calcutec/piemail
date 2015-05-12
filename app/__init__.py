import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, \
    MAIL_PASSWORD, UPLOAD_FOLDER, CACHE_FOLDER, MAX_CONTENT_LENGTH, \
    UPLOAD_FOLDER_NAME, SQLALCHEMY_DATABASE_URI
from .momentjs import momentjs

app = Flask(__name__)
app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_NAME'] = UPLOAD_FOLDER_NAME
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = 'Please log in to access this page.'
mail = Mail(app)


if os.environ.get('HEROKU') is not None:
    app.config['IMAGES_PATH'] = ['static/heroku_user_imgs']
    app.config['OAUTH_CREDENTIALS'] = {
        'facebook': {
            'id': '951231784910539',
            'secret': '724087cd0eef6537c5c16de5fda059f3'
        },
        'google': {
            'id': '908522697326-0gdm0ngo4397jb6m6s92fe5okfot344h.apps.googleusercontent.com',
            'secret': 'swr5Rj2E4f1O9xHjkp_T-TUk'
        }
    }
else:
    app.config['IMAGES_PATH'] = ['static/user_imgs']
    app.config['OAUTH_CREDENTIALS'] = {
        'facebook': {
            'id': '953764817990569',
            'secret': '5cca625e8873272007b723736bb4ed3b'
        },
        'google': {
            'id': "1019317791133-9kqnupafvmhcgivbpmhoaviclkrs2jgt.apps.googleusercontent.com",
            'secret': "6gcUnBwYLCxaXF0ofwfEsbXk"
        }
    }

app.config['IMAGES_CACHE'] = CACHE_FOLDER



from flask.json import JSONEncoder


class CustomJSONEncoder(JSONEncoder):
    """This class adds support for lazy translation texts to Flask's
    JSON encoder. This is necessary when flashing translated texts."""
    def default(self, obj):
        from speaklater import is_lazy_string
        if is_lazy_string(obj):
            try:
                return unicode(obj)  # python 2
            except NameError:
                return str(obj)  # python 3
        return super(CustomJSONEncoder, self).default(obj)

app.json_encoder = CustomJSONEncoder

if not app.debug and MAIL_SERVER != '':
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT),
                               'no-reply@' + MAIL_SERVER, ADMINS,
                               'burtonblog failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

if not app.debug and os.environ.get('HEROKU') is None:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/burtonblog.log', 'a',
                                       1 * 1024 * 1024, 10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('burtonblog startup')

if os.environ.get('HEROKU') is not None:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('burtonblog startup')

app.jinja_env.globals['momentjs'] = momentjs

app.config["S3_LOCATION"] = 'https://s3.amazonaws.com/netbardus/'
app.config["S3_KEY"] = 'AKIAIACI76P6VC7MIQRA'
app.config["S3_SECRET"] = '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'
app.config["S3_UPLOAD_DIRECTORY"] = 'css'
app.config["S3_BUCKET"] = 'netbardus'

from app import views, models
