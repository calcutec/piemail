# -*- coding: utf8 -*-
import os
CSRF_ENABLED = False
WTF_CSRF_ENABLED = False
basedir = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY = "For my eyes only"


# SQLALCHEMY_DATABASE_URI = os.environ['PIEMAIL_DATABASE_URL']
# SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
# SQLALCHEMY_RECORD_QUERIES = True
# administrator list
ADMINS = ['burton.wj@gmail.com']
