import boto
from PIL import Image
from app import app
from config import ALLOWED_EXTENSIONS
from forms import SignupForm, EditForm, PostForm, CommentForm, LoginForm
from rauth import OAuth2Service
import json
import urllib2
import cStringIO
from flask import request, redirect, url_for, render_template, g, flash
from flask.views import View
from flask.ext.login import login_required
from models import User, Post
from functools import wraps


class ViewData(object):
    def __init__(self, page_mark, slug=None, nickname=None, page=1, form=None, render_form=None, posts_for_page=200):
        self.posts_for_page = posts_for_page
        self.slug = slug
        self.nickname = nickname
        self.page = page
        self.page_mark = page_mark
        self.template_name = "base_template.html"
        self.title = page_mark.title()
        self.page_logo = "img/icons/" + page_mark + ".svg"
        self.form = form
        self.render_form = render_form
        self.profile_user = None
        self.posts = None
        self.post = None
        self.assets = {}
        self.context = None

        self.get_items()
        self.get_context()

    def get_items(self):
        if self.page_mark == 'profile':
            self.profile_user = User.query.filter_by(nickname=self.nickname).first()
            self.posts = Post.query.filter_by(author=self.profile_user)\
                .order_by(Post.timestamp.desc()).paginate(self.page, self.posts_for_page, False)
            if not self.form:
                self.assets['header_form'] = self.get_form()

        elif self.page_mark == 'home':
            self.assets['header_text'] = "Home Page"

        elif self.page_mark == 'members':
            self.posts = User.query.all()
            self.assets['header_text'] = "Members on this site"

        elif self.page_mark == 'poetry':
            self.posts = Post.query.filter_by(writing_type="featured")\
                .order_by(Post.timestamp.desc()).paginate(self.page, self.posts_for_page, False)
            self.assets['header_text'] = "Poetry Page"

        elif self.page_mark == 'workshop':
            self.posts = Post.query.filter_by(writing_type="poem")\
                .order_by(Post.timestamp.desc()).paginate(self.page, self.posts_for_page, False)
            self.assets['header_text'] = "Workshop Page"

        elif self.page_mark == 'portfolio':
            self.posts = g.user.posts\
                .order_by(Post.timestamp.desc()).paginate(self.page, self.posts_for_page, False)
            if not self.form:
                self.assets['header_form'] = self.get_form()

        elif self.page_mark == 'detail':
            self.post = Post.query.filter(Post.slug == self.slug).first()
            self.assets['header_text'] = "Poem Details"
            if not self.form:
                self.assets['body_form'] = self.get_form()

        elif self.page_mark == 'signup':
            self.assets['header_text'] = "Signup Page"
            if not self.form:
                self.assets['body_form'] = self.get_form()

        elif self.page_mark == 'login':
            self.assets['header_text'] = "Login Page"
            if not self.form:
                self.assets['body_form'] = self.get_form()

        elif self.page_mark == 'phonegap':
            self.posts = User.query.all()
            self.assets['header_text'] = "PhoneGap Page"
            self.template_name = "index.html"

        elif self.page_mark == 'piemail':
            self.assets['header_text'] = "PhoneGap Page"
            self.template_name = "piemail.html"

    def get_form(self):
        rendered_form = None
        if self.page_mark == 'signup':
            self.form = SignupForm()
            rendered_form = render_template("assets/forms/signup_form.html", form=self.form)
        elif self.page_mark == 'login':
            self.form = LoginForm()
            rendered_form = render_template("assets/forms/login_form.html", form=self.form)
        elif self.page_mark == 'profile':
            self.form = EditForm()
            self.form.nickname.data = g.user.nickname
            self.form.about_me.data = g.user.about_me
            if self.render_form:  # Only render profile form on request, using button to show on noJS profile page
                rendered_form = render_template("assets/forms/profile_form.html", form=self.form)
        elif self.page_mark == 'portfolio':
            self.form = PostForm()
            if self.render_form: # Only render post form on request, using button to show on noJS portfolio page
                rendered_form = render_template("assets/forms/poem_form.html", form=self.form)
        elif self.page_mark == 'detail':
            self.form = CommentForm()
            rendered_form = render_template("assets/forms/comment_form.html", form=self.form)
        return rendered_form

    def get_context(self):
        self.context = {'post': self.post, 'posts': self.posts, 'title': self.title, 'profile_user': self.profile_user,
                        'page_logo': self.page_logo, 'page_mark': self.page_mark, 'form': self.form,
                        'assets': self.assets}


def check_expired(func):
    @wraps(func)
    def decorated_function(page_mark=None, slug=None, post_id=None):
        if page_mark and page_mark not in ['poetry', 'portfolio', 'workshop', 'create']:
            flash("That page does not exist.")
            return redirect(url_for('home'))
        return func(page_mark, slug, post_id)

    return decorated_function


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def pre_upload(img_obj):
    thumbnail_name, thumbnail_file, upload_directory = generate_thumbnail(**img_obj)
    s3_file_name = s3_upload(thumbnail_name, thumbnail_file, upload_directory)
    return s3_file_name


def s3_upload(filename, source_file, upload_directory, acl='public-read'):
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

    sml = b.new_key("/".join([upload_directory, filename]))
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
    if photo_type == 'thumbnail':
        upload_directory = "cordova/www/pics"
    else:
        upload_directory = "user_imgs"
    image_stream = cStringIO.StringIO()
    img.save(image_stream, extension, quality=75)
    image_stream.seek(0)
    thumbnail_file = image_stream
    return thumbnail_name, thumbnail_file, upload_directory


class GenericListView(View):
    def __init__(self, view_data):
        self.view_data = view_data

    def get_template_name(self):
        return self.view_data.template_name

    def get_context(self):
        context = self.view_data.context
        return context

    def dispatch_request(self):
        context = self.get_context()
        return self.render_template(context)

    def render_template(self, context):
        return render_template(self.get_template_name(), **context)


class LoginRequiredListView(GenericListView):
    decorators = [login_required]


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
        return url_for('login', provider=self.provider_name,
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
        nickname = me.get('email').split('@')[0]
        nickname = User.make_valid_nickname(nickname)
        nickname = User.make_unique_nickname(nickname)
        return nickname, me.get('email')


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
                  'redirect_uri': self.get_callback_url()},
            decoder=json.loads
        )
        me = oauth_session.get('').json()
        nickname = me['name']
        nickname = User.make_valid_nickname(nickname)
        nickname = User.make_unique_nickname(nickname)
        return nickname, me['email']
