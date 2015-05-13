import os
import boto
from PIL import Image
from app import app
from rauth import OAuth2Service
import json
import urllib2
import cStringIO
from flask import request, redirect, url_for


def pre_upload(img_obj):
    thumbnail_name, thumbnail_file = generate_thumbnail(**img_obj)
    s3_file_name = s3_upload(thumbnail_name, thumbnail_file)
    return s3_file_name


def s3_upload(filename, source_file, acl='public-read'):
    """ Uploads WTForm File Object to Amazon S3

        Expects following app.config attributes to be set:
            S3_KEY              :   S3 API Key
            S3_SECRET           :   S3 Secret Key
            S3_BUCKET           :   What bucket to upload to
            S3_UPLOAD_DIRECTORY :   Which S3 Directory.

        The default sets the access rights on the uploaded file to
        public-read.  Optionally, can generate a unique filename via
        the uuid4 function combined with the file extension from
        the source file(to avoid filename collision for user uploads.
    """

    # Connect to S3 and upload file.
    conn = boto.connect_s3(app.config["AWS_ACCESS_KEY_ID"], app.config["AWS_SECRET_ACCESS_KEY"])
    b = conn.get_bucket(app.config["S3_BUCKET"])

    sml = b.new_key("/".join([app.config["S3_UPLOAD_DIRECTORY"], filename]))
    sml.set_contents_from_file(source_file, rewind=True)
    sml.set_acl(acl)

    return filename


def generate_thumbnail(filename, img, box, photo_type, crop, extension):
    """Downsample the image.
    @param box: tuple(x, y) - the bounding box of the result image
    """
    # preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *= 2
    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)

    # calculate the cropping box and get the cropped part
    if crop:
        x1 = y1 = 0
        x2, y2 = img.size
        wratio = 1.0 * x2/box[0]
        hratio = 1.0 * y2/box[1]
        if hratio > wratio:
            y1 = int(y2/2-box[1]*wratio/2)
            y2 = int(y2/2+box[1]*wratio/2)
        else:
            x1 = int(x2/2-box[0]*hratio/2)
            x2 = int(x2/2+box[0]*hratio/2)
        img = img.crop((x1, y1, x2, y2))

    # Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Image.ANTIALIAS)

    # save it into a file-like object
    thumbnail_name = photo_type + "_" + filename
    image_stream = cStringIO.StringIO()
    img.save(image_stream, extension, quality=75)
    image_stream.seek(0)
    thumbnail_file = image_stream
    return thumbnail_name, thumbnail_file


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(cls, provider_name):
        if cls.providers is None:
            cls.providers = {}
            for provider_class in cls.__subclasses__():
                provider = provider_class()
                cls.providers[provider.provider_name] = provider
        return cls.providers[provider_name]


class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()}
        )
        me = oauth_session.get('me').json()
        return me.get('email').split('@')[0], me.get('email')


class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        googleinfo = urllib2.urlopen('https://accounts.google.com/.well-known/openid-configuration')
        google_params = json.load(googleinfo)
        self.service = OAuth2Service(
                name='google',
                client_id=self.consumer_id,
                client_secret=self.consumer_secret,
                authorize_url=google_params.get('authorization_endpoint'),
                base_url=google_params.get('userinfo_endpoint'),
                access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
            )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
                data={'code': request.args['code'],
                      'grant_type': 'authorization_code',
                      'redirect_uri': self.get_callback_url()
                     },
                decoder=json.loads
        )
        me = oauth_session.get('').json()
        return me['name'], me['email']