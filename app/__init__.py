import os
from flask import Flask
from .momentjs import momentjs
from flask_wtf.csrf import CsrfProtect

app = Flask(__name__)
app.config.from_object('config')
CsrfProtect(app)


if os.environ.get('HEROKU') is not None:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('burtonblog startup')


# app.config["S3_LOCATION"] = 'https://s3.amazonaws.com/netbardus/'
# app.config["S3_UPLOAD_DIRECTORY"] = 'user_imgs'
# app.config["S3_BUCKET"] = 'netbardus'
# app.config["AWS_ACCESS_KEY_ID"] = os.environ['AWS_ACCESS_KEY_ID']
# app.config["AWS_SECRET_ACCESS_KEY"] = os.environ['AWS_SECRET_ACCESS_KEY']

from app import views