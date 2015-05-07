# -*- coding: utf8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = ('sqlite:///' + os.path.join(basedir, 'app.db') +
                               '?check_same_thread=False')
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_RECORD_QUERIES = True
WHOOSH_BASE = os.path.join(basedir, 'search.db')

# Whoosh does not work on Heroku
WHOOSH_ENABLED = os.environ.get('HEROKU') is None

# slow database query threshold (in seconds)
DATABASE_QUERY_TIMEOUT = 0.5

# image upload folder and allowed extensions
if os.environ.get('HEROKU') is None:
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/user_imgs')
    CACHE_FOLDER = os.path.join(basedir, 'app/static/img_cache')
    UPLOAD_FOLDER_NAME = "user_imgs/"
else:
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/heroku_user_imgs')
    CACHE_FOLDER = os.path.join(basedir, 'app/static/heroku_img_cache')
    UPLOAD_FOLDER_NAME = "heroku_user_imgs/"

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# email server
MAIL_SERVER = 'smtp.googlemail.com'  # your mailserver
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# available languages
LANGUAGES = {
    'en': 'English',
    'es': 'Español'
}


# administrator list
ADMINS = ['burton.wj@gmail.com']

# pagination
POSTS_PER_PAGE = 3
MAX_SEARCH_RESULTS = 50
