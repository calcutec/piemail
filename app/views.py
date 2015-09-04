from flask import render_template, flash, redirect, session, url_for, request, g, abort, jsonify
from werkzeug.utils import secure_filename
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.sqlalchemy import get_debug_queries
from datetime import datetime
from app import app, db, lm
from config import DATABASE_QUERY_TIMEOUT
from slugify import slugify
from .forms import SignupForm, LoginForm, EditForm, PostForm, SearchForm, CommentForm
from .models import User, Post, Comment
from .emails import follower_notification
from .utils import OAuthSignIn, pre_upload, ViewData, allowed_file
from PIL import Image
import json
from flask.views import MethodView
import os
basedir = os.path.abspath(os.path.dirname(__file__))


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('members'))


@app.route('/logout', methods=['GET'])
def logout():
        logout_user()
        return redirect(url_for('login'))


class SignupAPI(MethodView):
    def get(self, form=None):
        if g.user is not None and g.user.is_authenticated():
            return redirect(url_for('members'))
        signup_data = ViewData("signup", form=form)
        return render_template(signup_data.template_name, **signup_data.context)

    def post(self):
        form = SignupForm()
        response = self.process_signup(form)
        return response

    def process_signup(self, form):
        if request.is_xhr:
            if form.validate_on_submit():
                result = {'iserror': False}
                newuser = self.save_user(form)
                result['savedsuccess'] = True
                result['newuser_nickname'] = newuser.nickname
                return json.dumps(result)
            else:
                form.errors['iserror'] = True
                return json.dumps(form.errors)
        else:
            if form.validate_on_submit():
                newuser = self.save_user(form)
                return redirect(url_for("members", nickname=newuser.nickname))
            else:
                signup_data = ViewData("signup", form=form)
                return render_template(signup_data.template_name, **signup_data.context)

    def save_user(self, form):
        newuser = User(form.firstname.data, form.email.data, firstname=form.firstname.data,
                       lastname=form.lastname.data,
                       password=form.password.data)
        db.session.add(newuser)
        db.session.add(newuser.follow(newuser))
        db.session.commit()
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(newuser, remember=remember_me)
        return newuser

signup_api_view = SignupAPI.as_view('signup')  # URLS for MEMBER API
app.add_url_rule('/signup/', view_func=signup_api_view, methods=["GET", "POST"])  # Display and Validate Signup Form


class LoginAPI(MethodView):
    def post(self):
        form = LoginForm()  # LOGIN VALIDATION
        if request.is_xhr:
            if form.validate_on_submit():
                result = {'iserror': False}
                returninguser = self.login_returning_user(form)
                result['savedsuccess'] = True
                result['returninguser_nickname'] = returninguser.nickname
                return json.dumps(result)
            else:
                form.errors['iserror'] = True
                return json.dumps(form.errors)
        else:
            if form.validate_on_submit():
                returninguser = self.login_returning_user(form)
                return redirect('/profile/' + returninguser.nickname)
            else:
                login_data = ViewData("login", form=form)
                return render_template(login_data.template_name, **login_data.context)

    def get(self, get_provider=None, provider=None):
        if get_provider is not None:    # GET OAUTH PROVIDER
            if not current_user.is_anonymous():
                return redirect(url_for('home'))
            oauth = OAuthSignIn.get_provider(get_provider)
            return oauth.authorize()
        elif provider is not None:  # OAUTH PROVIDER CALLBACK
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
            return redirect(request.args.get('next') or url_for('members'))
        else:   # LOGIN PAGE
            if g.user is not None and g.user.is_authenticated():
                return redirect(url_for('members'))
            login_data = ViewData("login")
            return render_template(login_data.template_name, **login_data.context)

    def login_returning_user(self, form):
        returninguser = User.query.filter_by(email=form.email.data).first()
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(returninguser, remember=remember_me)
        return returninguser

login_api_view = LoginAPI.as_view('login')  # Urls for Login API
# Authenticate user
app.add_url_rule('/login/', view_func=login_api_view, methods=["GET", "POST"])
# Oauth login
app.add_url_rule('/login/<get_provider>', view_func=login_api_view, methods=["GET", ])
# Oauth provider callback
app.add_url_rule('/callback/<provider>', view_func=login_api_view, methods=["GET", ])


class MembersAPI(MethodView):
    def post(self, nickname=None):
        if nickname is None:  # Read all members
            view_data = ViewData('home')
            return render_template(view_data.template_name, **view_data.context)
        else:
            form = EditForm()  # Update Member Data
            response = self.update_user(form)
            return response

    @login_required
    def get(self, nickname=None, action=None):
        if action == 'update':
            form = EditForm()
            form.nickname.data = g.user.nickname
            form.about_me.data = g.user.about_me
            profile_data = ViewData("update", form=form)
            return render_template(profile_data.template_name, **profile_data.context)
        elif action == 'follow':
            user = User.query.filter_by(nickname=nickname).first()
            if user is None:
                flash('User %s not found.' % nickname)
                return redirect(url_for('home'))
            if user == g.user:
                flash('You can\'t follow yourself!')
                return redirect(url_for('members', nickname=nickname))
            u = g.user.follow(user)
            if u is None:
                flash('Cannot follow %s.' % nickname)
                return redirect(url_for('members', nickname=nickname))
            db.session.add(u)
            db.session.commit()
            flash('You are now following %s.' % nickname)
            follower_notification(user, g.user)
            return redirect(url_for('members', nickname=nickname))
        elif action == 'unfollow':
            user = User.query.filter_by(nickname=nickname).first()
            if user is None:
                flash('User %s not found.' % nickname)
                return redirect(url_for('home'))
            if user == g.user:
                flash('You can\'t unfollow yourself!')
                return redirect(url_for('members', nickname=nickname))
            u = g.user.unfollow(user)
            if u is None:
                flash('Cannot unfollow %s.' % nickname)
                return redirect(url_for('members', nickname=nickname))
            db.session.add(u)
            db.session.commit()
            flash('You have stopped following %s.' % nickname)
            profile_data = ViewData("profile", nickname=nickname)
            return render_template(profile_data.template_name, **profile_data.context)
        elif nickname is None:  # Display all members
            view_data = ViewData('home')
            return render_template(view_data.template_name, **view_data.context)
        else:  # Display a single member
            profile_data = ViewData("profile", nickname=nickname)
            return render_template(profile_data.template_name, **profile_data.context)

    @login_required
    def delete(self, nickname):
        pass

    @login_required
    def update_user(self, form):
        if request.is_xhr:  # First validate form using an async request
            if form.validate(g.user):
                result = {'iserror': False, 'savedsuccess': True}
                return json.dumps(result)
            form.errors['iserror'] = True
            return json.dumps(form.errors)
        else:  # Once form is valid, original form is called and processed
            if form.validate(g.user):
                profile_photo = request.files['profile_photo']
                if profile_photo and allowed_file(profile_photo.filename):
                    filename = secure_filename(profile_photo.filename)
                    img_obj = dict(filename=filename, img=Image.open(profile_photo.stream), box=(400, 300),
                                   photo_type="thumb", crop=True,
                                   extension=form['profile_photo'].data.mimetype.split('/')[1].upper())
                    profile_photo_name = pre_upload(img_obj)
                    g.user.profile_photo = profile_photo_name
                g.user.nickname = form.nickname.data
                g.user.about_me = form.about_me.data
                db.session.add(g.user)
                db.session.commit()
                return redirect("/profile/" + g.user.nickname)
            profile_data = ViewData("profile", nickname=g.user.nickname, form=form)
            return render_template(profile_data.template_name, **profile_data.context)


member_api_view = MembersAPI.as_view('members')  # URLS for MEMBER API
# Read, Update and Destroy a single member
app.add_url_rule('/profile/<nickname>', view_func=member_api_view, methods=["GET", "POST", "PUT", "DELETE"])
# Read all members
app.add_url_rule('/profile/', view_func=member_api_view, methods=["GET", "POST"])
# Update a member when JS is turned off)
app.add_url_rule('/profile/<action>/<nickname>', view_func=member_api_view, methods=["GET"])


class PostAPI(MethodView):
    decorators = [login_required]

    def post(self, page_mark=None, action=None, post_id=None):
        if page_mark and page_mark not in ['poetry', 'portfolio', 'workshop', 'create', 'detail']:
            flash("That page does not exist.")
            return redirect(url_for('posts', page_mark='portfolio'))

        if action == 'vote':   # Vote on post
            post_id = post_id
            user_id = g.user.id
            if not post_id:
                abort(404)
            post = Post.query.get_or_404(int(post_id))
            vote_status = post.vote(user_id=user_id)
            return jsonify(new_votes=post.votes, vote_status=vote_status)
        elif action == 'comment':   # Comment on post
            form = CommentForm()
            if request.is_xhr:
                if form.validate_on_submit():
                    result = {'iserror': False}
                    comment = Comment(created_at=datetime.utcnow(), user_id=g.user.id, body=form.comment.data,
                                      post_id=post_id)
                    db.session.add(comment)
                    db.session.commit()
                    result['savedsuccess'] = True
                    result['new_comment'] = render_template('comps/detail/comment.html', comment=comment)
                    return json.dumps(result)
                form.errors['iserror'] = True
                return json.dumps(form.errors)
            else:
                if form.validate_on_submit():
                    comment = Comment(created_at=datetime.utcnow(), user_id=g.user.id, body=form.comment.data,
                                      post_id=post_id)
                    db.session.add(comment)
                    db.session.commit()
                    post = Post.query.get(post_id)
                    return redirect(url_for('posts', page_mark='detail', slug=post.slug))
        elif post_id is None:  # Create a new post
            form = PostForm()
            if form.validate_on_submit():
                result = {'iserror': False}
                slug = slugify(form.header.data)
                post = Post(body=form.body.data, timestamp=datetime.utcnow(),
                            author=g.user, photo=None, thumbnail=None, header=form.header.data,
                            writing_type=form.writing_type.data, slug=slug)
                db.session.add(post)
                db.session.commit()
                if request.is_xhr:
                    result['savedsuccess'] = True
                    result['new_poem'] = render_template('comps/post.html', page_mark=page_mark, post=post, g=g)
                    return json.dumps(result)
                else:
                    return redirect("/detail/" + post.slug)
            else:
                if request.is_xhr:
                    form.errors['iserror'] = True
                    return json.dumps(form.errors)
                else:
                    return form.errors

    def get(self, page_mark=None, action=None, slug=None, post_id=None):
        if page_mark and page_mark not in ['poetry', 'portfolio', 'workshop', 'create', 'detail']:
            flash("That page does not exist.")
            return redirect(url_for('posts', page_mark='portfolio'))
        if action == 'create':  # Create a new post
            form = PostForm()
            page_mark = 'create'
            view_data = ViewData(page_mark, form)
            return render_template(view_data.template_name, **view_data.context)
        elif action == 'delete':
            post = Post.query.get(post_id)
            db.session.delete(post)
            db.session.commit()
            return redirect(url_for('posts', page_mark='workshop'))
        elif action == 'vote':   # Vote on post
            post_id = post_id
            user_id = g.user.id
            if not post_id:
                abort(404)
            post = Post.query.get_or_404(int(post_id))
            post.vote(user_id=user_id)
            return redirect(url_for('posts', page_mark='detail', slug=post.slug))
        elif slug is None:    # Read all posts
            view_data = ViewData(page_mark)
            return render_template(view_data.template_name, **view_data.context)
        elif slug is not None:       # Read a single post
            detail_data = ViewData("detail", slug=slug)
            return render_template(detail_data.template_name, **detail_data.context)

    # Update Post
    def put(self):
        form = PostForm()
        if form.validate_on_submit():
            update_post = Post.query.get(request.form['post_id'])
            update_post.body = request.form['content']
            db.session.commit()
            result = {'updatedsuccess': True}
            return json.dumps(result)

    # Delete Post
    def delete(self, post_id):
        post = Post.query.get(post_id)
        db.session.delete(post)
        db.session.commit()
        result = {'deletedsuccess': True}
        return json.dumps(result)


# urls for Post API
post_api_view = PostAPI.as_view('posts')

# Create a single post, Read all posts (Restful)
app.add_url_rule('/<page_mark>/', view_func=post_api_view, methods=["POST", "GET"])
# Get, Update or Delete a single post (Restful)
app.add_url_rule('/<page_mark>/<int:post_id>', view_func=post_api_view, methods=["GET", "PUT", "DELETE"])
# Get a single post (NoJS)
app.add_url_rule('/<page_mark>/<slug>/', view_func=post_api_view, methods=["GET"])
# Create, Delete, Vote on, Comment on a single post post (NoJS)
app.add_url_rule('/<page_mark>/<action>/<int:post_id>', view_func=post_api_view, methods=["GET", "POST"])


# Helper functions
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
