import os
basedir = os.path.abspath(os.path.dirname(__file__))
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, session, url_for, request, g

from flask.ext.login import login_user, logout_user, current_user, \
    login_required
from flask.ext.sqlalchemy import get_debug_queries
from datetime import datetime
from app import app, db, lm, oid

from .forms import LoginForm, EditForm, PostForm, SearchForm, CommentForm
from .models import User, Post, Comment
from .emails import follower_notification
from .utils import generate_thumbnail
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, \
    DATABASE_QUERY_TIMEOUT

from rauth import OAuth2Service
from slugify import slugify


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()


@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning(
                "SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
                (query.statement, query.parameters, query.duration,
                 query.context))
    return response


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    page_mark = 'login'
    page_logo = 'img/icons/login.svg'
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           page_mark=page_mark,
                           page_logo=page_logo,
                           providers=app.config['OPENID_PROVIDERS'])


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():
    page_mark = 'home'
    page_logo = 'img/icons/home.svg'
    return render_template('index.html',
                           title='Home',
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/favorites', methods=['GET', 'POST'])
@app.route('/favorites/<int:page>', methods=['GET', 'POST'])
@login_required
def favorites(page=1):
    form = PostForm()
    if form.validate_on_submit():
        thumbnail_name = ''
        filename = secure_filename(form.photo.data.filename)
        slug = slugify(form.header.data)
        if filename is not None and filename is not '':
            filename_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(filename_path)
            thumbnail_name = generate_thumbnail(filename=filename, filename_path=filename_path, box=(80, 80),
                                                photo_type="thumb", crop=True)

        post = Post(body=form.post.data, timestamp=datetime.utcnow(),
                    author=g.user, photo=filename, thumbnail=thumbnail_name, header=form.header.data, slug=slug)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('favorites'))
    # favorite_posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    posts = g.user.all_posts().paginate(page, POSTS_PER_PAGE, False)
    page_mark = 'forum'
    page_logo = 'img/icons/forum.svg'
    return render_template('favorites.html',
                           title='Favorites',
                           form=form,
                           posts=posts,
                           page_mark=page_mark,
                           page_logo=page_logo,
                           upload_folder_name=app.config['UPLOAD_FOLDER_NAME'])


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %(nickname)s not found.', nickname=nickname)
        return redirect(url_for('index'))
    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
    page_mark = 'profile'
    page_logo = 'img/icons/profile.svg'
    return render_template('user.html',
                           user=user,
                           page_mark=page_mark,
                           page_logo=page_logo,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        filename = secure_filename(form.profile_photo.data.filename)
        if filename != None and filename != '':
            filename_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.profile_photo.data.save(filename_path)
            profile_photo = generate_thumbnail(filename=filename, filename_path=filename_path, box=(128, 128),
                                                photo_type="thumb", crop=True)
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        g.user.about_me = form.about_me.data
        g.user.profile_photo = profile_photo
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user'))
    elif request.method != "POST":
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    page_mark = 'profile'
    page_logo = 'img/icons/profile.svg'
    return render_template('edit.html',
                           form=form,
                           page_mark=page_mark,
                           page_logo=page_logo)

# @oid.after_login
# def after_login(resp):
#     if resp.email is None or resp.email == "":
#         flash(gettext('Invalid login. Please try again.'))
#         return redirect(url_for('login'))
#     user = User.query.filter_by(email=resp.email).first()
#     if user is None:
#         nickname = resp.nickname
#         if nickname is None or nickname == "":
#             nickname = resp.email.split('@')[0]
#         nickname = User.make_valid_nickname(nickname)
#         nickname = User.make_unique_nickname(nickname)
#         user = User(nickname=nickname, email=resp.email)
#         db.session.add(user)
#         db.session.commit()
#         # make the user follow him/herself
#         db.session.add(user.follow(user))
#         db.session.commit()
#     remember_me = False
#     if 'remember_me' in session:
#         remember_me = session['remember_me']
#         session.pop('remember_me', None)
#     login_user(user, remember=remember_me)
#     return redirect(request.args.get('next') or url_for('index'))

@app.route("/detail/<slug>", methods=['GET', 'POST'])
def posts(slug):
    post = Post.query.filter(Post.slug==slug).first()
    form = CommentForm()
    context = {"post": post, "form": form, "upload_folder_name":app.config['UPLOAD_FOLDER_NAME']}
    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, created_at=datetime.utcnow(), user_id=g.user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('posts', slug=slug))
    return render_template('posts/detail.html', **context)


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow %(nickname)s.', nickname=nickname)
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following %(nickname)s!', nickname=nickname)
    follower_notification(user, g.user)
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow %(nickname)s.', nickname=nickname)
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following %(nickname)s.',
                  nickname=nickname)
    return redirect(url_for('user', nickname=nickname))


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post not found.')
        return redirect(url_for('index'))
    if post.author.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.')
    return redirect(url_for('favorites'))


@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    upload_folder_name = app.config['UPLOAD_FOLDER_NAME']
    return render_template('search_results.html',
                           query=query,
                           results=results,
                           upload_folder_name=upload_folder_name)


current_app = app

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
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
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


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
        return (
            'facebook$' + me['id'],
            me.get('email').split('@')[0],  # Facebook does not provide
                                            # username, so the email's user
                                            # is used instead
            me.get('email')
        )


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
        # make the user follow him/herself
        db.session.add(user.follow(user))
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


