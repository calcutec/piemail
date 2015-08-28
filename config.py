# -*- coding: utf8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = os.environ['FLASK_SECRET_KEY']


SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_RECORD_QUERIES = True

WHOOSH_BASE = os.path.join(basedir, 'search.db')
# Whoosh does not work on Heroku
WHOOSH_ENABLED = os.environ.get('HEROKU') is None

# slow database query threshold (in seconds)
DATABASE_QUERY_TIMEOUT = 0.5

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# email server
MAIL_SERVER = 'smtp.googlemail.com'  # your mailserver
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# administrator list
ADMINS = ['burton.wj@gmail.com']

# pagination
POSTS_PER_PAGE = 500
MAX_SEARCH_RESULTS = 50
