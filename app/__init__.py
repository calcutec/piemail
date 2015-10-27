import os
from flask import Flask
from .momentjs import momentjs

app = Flask(__name__)
app.config.from_object('config')


# app.config["S3_LOCATION"] = 'https://s3.amazonaws.com/netbardus/'
# app.config["S3_UPLOAD_DIRECTORY"] = 'user_imgs'
# app.config["S3_BUCKET"] = 'netbardus'
# app.config["AWS_ACCESS_KEY_ID"] = os.environ['AWS_ACCESS_KEY_ID']
# app.config["AWS_SECRET_ACCESS_KEY"] = os.environ['AWS_SECRET_ACCESS_KEY']

from app import views