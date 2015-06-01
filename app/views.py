import os
basedir = os.path.abspath(os.path.dirname(__file__))
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, session, url_for, request, g, abort, jsonify

from flask.ext.login import login_user, logout_user, current_user, \
    login_required
from flask.ext.sqlalchemy import get_debug_queries
from datetime import datetime
from app import app, db, lm
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, \
    DATABASE_QUERY_TIMEOUT
from slugify import slugify

from .forms import SignupForm, LoginForm, EditForm, PostForm, SearchForm, CommentForm
from .models import User, Post, Comment
from .emails import follower_notification
from .utils import OAuthSignIn, pre_upload
from PIL import Image
import json

from flask.views import View, MethodView


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

class ViewData(object):
    def __init__(self, page_mark, slug=None, nickname=None):
        self.slug = slug
        self.page = 1
        self.page_mark = page_mark
        self.template_name = page_mark + ".html"
        self.form = self.get_form()
        self.title = page_mark.title()
        self.page_logo = "img/icons/" + page_mark + ".svg"
        self.profile_user = None
        if nickname is not None:
            self.profile_user = User.query.filter_by(nickname=nickname).first()
        else:
            self.profile_user = None
        if slug is not None:
            self.post = self.get_items()
            self.items = None
        else:
            self.items = self.get_items()
            self.post = None
        self.context = self.get_context()

    def get_items(self):
        if self.page_mark == 'home':
            self.items = Post.query.filter_by(writing_type="op-ed")
            return self.items
        if self.page_mark == 'poetry':
            self.items = Post.query.filter_by(writing_type="selected").paginate(self.page, POSTS_PER_PAGE, False)
            return self.items
        if self.page_mark == 'workshop':
            self.items = Post.query.filter_by(writing_type="poem").paginate(self.page, POSTS_PER_PAGE, False)
            return self.items
        if self.page_mark == 'portfolio':
            self.items = g.user.posts.paginate(1, POSTS_PER_PAGE, False)
            return self.items
        if self.page_mark == 'detail':
            self.post = Post.query.filter(Post.slug == self.slug).first()
            return self.post
        if self.page_mark == 'profile':
            self.items = self.profile_user.posts.paginate(self.page, POSTS_PER_PAGE, False)
            return self.items

    def get_form(self):
        if self.page_mark == 'portfolio':
            form = PostForm()
        elif self.page_mark == 'detail':
            form = CommentForm()
        else:
            form = None
        return form

    def get_context(self):
        context = {'post': self.post, 'posts': self.items, 'title': self.title, 'profile_user': self.profile_user,
                   'page_logo': self.page_logo, 'page_mark': self.page_mark, 'form': self.form}
        return context


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('home'))

home_data = ViewData("home")
app.add_url_rule('/home/', view_func=GenericListView.as_view('home', home_data), methods=["GET", ])

poetry_data = ViewData("poetry")
app.add_url_rule('/poetry/', view_func=GenericListView.as_view('poetry', poetry_data), methods=["GET", ])

workshop_data = ViewData("workshop")
app.add_url_rule('/workshop/', view_func=LoginRequiredListView.as_view('workshop', workshop_data), methods=["GET", ])

@app.route('/portfolio/', methods=['GET', ])
@login_required
def portfolio():
    portfolio_data = ViewData("portfolio")
    return render_template(portfolio_data.template_name, **portfolio_data.context)

class PostAPI(MethodView):
    decorators = [login_required]

    # Create a new Post
    def post(self):
        form = PostForm(request.form)
        if form.validate():
            result = {'iserror': False}
            slug = slugify(form.header.data)
            try:
                post = Post(body=form.post.data, timestamp=datetime.utcnow(),
                            author=g.user, photo=None, thumbnail=None, header=form.header.data,
                            writing_type=form.writing_type.data, slug=slug)
                db.session.add(post)
                db.session.commit()
                result['savedsuccess'] = True
            except:
                result['savedsuccess'] = False
            result['new_poem'] = render_template('post.html', page_mark='detail', post=post, g=g)
            return json.dumps(result)
        form.errors['iserror'] = True
        return json.dumps(form.errors)

    # Read a single Post
    def get(self, slug):
        detail_data = ViewData("detail", slug)
        if detail_data.form.validate_on_submit():
            comment = Comment(created_at=datetime.utcnow(), user_id=g.user.id, body=detail_data.form.comment.data, post_id=detail_data.post.id)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment is now live!')
            return redirect(url_for('posts', slug=slug))
        return render_template(detail_data.template_name, **detail_data.context)

    # Update Post
    def put(self, post_id):
        update_post = Post.query.get(request.form['post_id'])
        update_post.body = request.form['content']
        db.session.commit()
        return request.form['content']

    # Delete Post
    def delete(self, post_id):
        result = {'deletedsuccess': True}
        try:
            post = Post.query.get(post_id)
            db.session.delete(post)
            db.session.commit()
        except:
            result['deletedsuccess'] = False
        return json.dumps(result)


# urls for Post API
post_api_view = PostAPI.as_view('detail')
# Create a new post
app.add_url_rule('/detail/', view_func=post_api_view, methods=["POST", ])
# Read a single post
app.add_url_rule('/detail/<slug>', view_func=post_api_view, methods=["GET", ])
# Update a single post
app.add_url_rule('/detail/<int:post_id>', view_func=post_api_view, methods=["PUT", ])
# Delete a single post
app.add_url_rule('/detail/<int:post_id>', view_func=post_api_view, methods=["DELETE", ])


# Vote on Post
@app.route('/vote/', methods=['POST'])
@login_required
def vote_poem():
    """
    Submit votes via ajax
    """
    post_id = int(request.form['post_id'])
    user_id = g.user.id
    if not post_id:
        abort(404)
    post = Post.query.get_or_404(int(post_id))
    vote_status = post.vote(user_id=user_id)
    return jsonify(new_votes=post.votes, vote_status=vote_status)


class UserAPI(MethodView):
    decorators = [login_required]

    # Create a new User
    def post(self):
        pass

    # Read a single profile
    def get(self, nickname):
        profile_data = ViewData("profile", nickname=nickname)
        return render_template(profile_data.template_name, **profile_data.context)

    # Update User
    def put(self, user_id):
        nickname = g.user.nickname
        profile_data = ViewData("profile", nickname)
        if profile_data.form.validate_on_submit():
            filename = secure_filename(profile_data.form.profile_photo.data.filename)
            if filename is not None and filename is not '':
                img_obj = dict(filename=filename, img=Image.open(request.files['profile_photo']), box=(128, 128),
                               photo_type="thumb", crop=True,
                               extension=profile_data.form['profile_photo'].data.mimetype.split('/')[1].upper())
                profile_photo_name = pre_upload(img_obj)
                g.user.profile_photo = profile_photo_name
            g.user.nickname = profile_data.form.nickname.data
            g.user.about_me = profile_data.form.about_me.data
            db.session.add(g.user)
            db.session.commit()
            flash('Your changes have been saved.')
            return redirect(url_for('profile', nickname=g.user.nickname))
        profile_data.form.nickname.data = g.user.nickname
        profile_data.form.about_me.data = g.user.about_me
        return render_template(profile_data.template_name, **profile_data.context)

    # Delete User
    def delete(self, post_id):
        pass


# urls for User API
user_api_view = UserAPI.as_view('profile')
# Create a new user
app.add_url_rule('/profile/', view_func=user_api_view, methods=["POST", ])
# Read a single user
app.add_url_rule('/profile/<nickname>', view_func=user_api_view, methods=["GET", ])
# Read multiple users
app.add_url_rule('/profile/', view_func=user_api_view, methods=["GET", ])
# Update a single user
app.add_url_rule('/profile/', view_func=user_api_view, methods=["PUT", ])
# Delete a single user
# app.add_url_rule('/profile/<int:user_id>', view_func=user_api_view, methods=["DELETE"])


@app.route('/profile', methods=['PUT'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        filename = secure_filename(form.profile_photo.data.filename)
        if filename is not None and filename is not '':
            img_obj = dict(filename=filename, img=Image.open(request.files['profile_photo']), box=(128, 128),
                           photo_type="thumb", crop=True,
                           extension=form['profile_photo'].data.mimetype.split('/')[1].upper())
            profile_photo_name = pre_upload(img_obj)
            # flash('{src} uploaded to S3'.format(src=profile_photo_name))
            g.user.profile_photo = profile_photo_name
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('profile', nickname=g.user.nickname))
    elif request.method != "POST":
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    page_mark = 'profile'
    page_logo = 'img/icons/profile.svg'
    return render_template('edit.html',
                           form=form,
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('home'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('profile', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow %s.' % nickname)
        return redirect(url_for('profile', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following %s.' % nickname)
    follower_notification(user, g.user)
    return redirect(url_for('profile', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('home'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('profile', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow %s.' % nickname)
        return redirect(url_for('profile', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following %s.' % nickname)
    return redirect(url_for('profile', nickname=nickname))

# User Signup and Login
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    form = SignupForm()

    if form.validate_on_submit():
        newuser = User(form.firstname.data, form.email.data, firstname=form.firstname.data, lastname=form.lastname.data,
                       password=form.password.data)
        db.session.add(newuser)
        db.session.add(newuser.follow(newuser))
        db.session.commit()
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(newuser, remember=remember_me)
        return redirect(url_for('portfolio', user_id=g.user.id))

    page_mark = 'signup'
    page_logo = 'img/icons/login.svg'
    return render_template('signup.html',
                           title='Sign In',
                           form=form,
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        newuser = User.query.filter_by(email=form.email.data).first()
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(newuser, remember=remember_me)
        return redirect(url_for('portfolio'))

    page_mark = 'login'
    page_logo = 'img/icons/login.svg'
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('home'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('home'))
    oauth = OAuthSignIn.get_provider(provider)
    nickname, email = oauth.callback()
    if email is None:
        flash('Authentication failed.')
        return redirect(url_for('home'))
    currentuser = User.query.filter_by(email=email).first()
    if not currentuser:
        currentuser = User(nickname=nickname, email=email)
        db.session.add(currentuser)
        db.session.add(currentuser.follow(currentuser))
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(currentuser, remember=remember_me)
    return redirect(request.args.get('next') or url_for('portfolio', user_id=currentuser.id))

# Search
@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('home'))
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


# Other Helpers
@app.context_processor
def inject_static_url():
    local_static_url = app.static_url_path
    static_url = 'https://s3.amazonaws.com/netbardus/'
    if os.environ.get('HEROKU') is not None:
        local_static_url = static_url
    if not static_url.endswith('/'):
        static_url += '/'
    if not local_static_url.endswith('/'):
        local_static_url += '/'
    return dict(
        static_url=static_url,
        local_static_url=local_static_url
    )


@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', error=error), 500
