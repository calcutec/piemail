import os
from flask import Flask
from .momentjs import momentjs
# from flask_wtf.csrf import CsrfProtect

app = Flask(__name__)
app.config.from_object('config')
# CsrfProtect(app)


if os.environ.get('HEROKU') is not None:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('burtonblog startup')


from app import views
