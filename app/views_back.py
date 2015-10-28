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
from .utils import OAuthSignIn, pre_upload, ViewData, allowed_file, GenericListView
from PIL import Image
import json
from flask.views import MethodView
import os
basedir = os.path.abspath(os.path.dirname(__file__))

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


# @app.route('/', methods=['GET'])
# def index():
#     return redirect(url_for('home'))


@app.route('/', methods=['GET'])
def index():
    return redirect("/piemail")

# phonegap_data = ViewData(page_mark="phonegap")
# app.add_url_rule('/phonegap/', view_func=GenericListView.as_view('phonegap', phonegap_data), methods=["GET", ])


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/employees', methods=['GET'])
@crossdomain(origin='*')
def employees():
        employee_dict = User.query.all()
        return jsonify(employees=[i.json_view() for i in employee_dict])


home_data = ViewData(page_mark="home")
app.add_url_rule('/home/', view_func=GenericListView.as_view('home', home_data), methods=["GET", ])


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
                return redirect(url_for('members', nickname=returninguser.nickname))
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
            return redirect(request.args.get('next') or '/piemail')
            # return redirect(request.args.get('next') or url_for('members'))
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
        form = EditForm()  # Update Member Data
        response = self.update_user(form)
        return response

    @login_required
    def get(self, nickname=None, action=None):
        if action == 'update':
            profile_data = ViewData(page_mark="profile", render_form=True, nickname=nickname)
            return render_template(profile_data.template_name, **profile_data.context)
        elif action == 'follow':
            user = User.query.filter_by(nickname=nickname).first()
            if user is None:
                flash('User %s not found.' % nickname)
                return redirect(url_for('home'))
            if user == g.user:
                flash('You can\'t follow yourself!')
                return redirect(redirect_url())
            u = g.user.follow(user)
            if u is None:
                flash('Cannot follow %s.' % nickname)
                return redirect(redirect_url())
            db.session.add(u)
            db.session.commit()
            flash('You are now following %s.' % nickname)
            follower_notification(user, g.user)
            profile_data = ViewData("profile", nickname=nickname)
            return render_template(profile_data.template_name, **profile_data.context)
        elif action == 'unfollow':
            user = User.query.filter_by(nickname=nickname).first()
            if user is None:
                flash('User %s not found.' % nickname)
                return redirect(redirect_url())
            if user == g.user:
                flash('You can\'t unfollow yourself!')
                return redirect(redirect_url())
            u = g.user.unfollow(user)
            if u is None:
                flash('Cannot unfollow %s.' % nickname)
                return redirect(redirect_url())
            db.session.add(u)
            db.session.commit()
            flash('You have stopped following %s.' % nickname)
            profile_data = ViewData("profile", nickname=nickname)
            return render_template(profile_data.template_name, **profile_data.context)
        elif nickname is None:  # Display all members
            if request.url_rule.rule == '/phonegap/':
                view_data = ViewData(page_mark='phonegap')
                return render_template(view_data.template_name, **view_data.context)
            if request.url_rule.rule == '/piemail/':
                view_data = ViewData(page_mark='piemail')
                return render_template(view_data.template_name, **view_data.context)
            else:
                if request.is_xhr:
                    employee_dict = User.query.all()
                    return jsonify(employees=[i.json_view() for i in employee_dict])
                else:
                    view_data = ViewData(page_mark='members')
                    return render_template(view_data.template_name, **view_data.context)
        else:  # Display a single member
            profile_data = ViewData(page_mark="profile", nickname=nickname)
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

                    thumbnail_obj = dict(filename=filename, img=Image.open(profile_photo.stream), box=(160, 160),
                                         photo_type="thumbnail", crop=True,
                                         extension=form['profile_photo'].data.mimetype.split('/')[1].upper())
                    thumbnail_name = pre_upload(thumbnail_obj)

                    g.user.profile_photo = profile_photo_name
                    g.user.thumbnail = thumbnail_name

                g.user.nickname = form.nickname.data
                g.user.about_me = form.about_me.data
                db.session.add(g.user)
                db.session.commit()
                profile_data = ViewData(page_mark="profile", nickname=g.user.nickname, form=form)
                return render_template(profile_data.template_name, **profile_data.context)
            profile_data = ViewData(page_mark="profile", nickname=g.user.nickname, form=form)
            return render_template(profile_data.template_name, **profile_data.context)


member_api_view = MembersAPI.as_view('members')  # URLS for MEMBER API
# Read, Update and Destroy a single member
app.add_url_rule('/members/<nickname>', view_func=member_api_view, methods=["GET", "POST", "PUT", "DELETE"])
# Read all members
app.add_url_rule('/members/', view_func=member_api_view, methods=["GET"])
app.add_url_rule('/phonegap/', view_func=member_api_view, methods=["GET"])
app.add_url_rule('/piemail/', view_func=member_api_view, methods=["GET"])
# Update a member when JS is turned off)
app.add_url_rule('/members/<action>/<nickname>', view_func=member_api_view, methods=["GET"])


class PostAPI(MethodView):
    # decorators = [login_required]

    def post(self, page_mark=None):
        form = PostForm()
        if form.validate_on_submit():
            slug = slugify(form.header.data)
            post = Post(body=form.body.data, timestamp=datetime.utcnow(),
                        author=g.user, photo=None, thumbnail=None, header=form.header.data,
                        writing_type=form.writing_type.data, slug=slug)
            db.session.add(post)
            db.session.commit()
            if request.is_xhr:
                response = post.json_view()
                response['savedsuccess'] = True
                return json.dumps(response)
            else:
                return redirect(url_for('posts', page_mark='portfolio'))
        else:
            if request.is_xhr:
                form.errors['iserror'] = True
                return json.dumps(form.errors)
            else:
                detail_data = ViewData(page_mark=page_mark, form=form)
                return render_template(detail_data.template_name, **detail_data.context)

    @login_required
    def get(self, page_mark=None, slug=None, post_id=None):
        if slug is None and post_id is None:    # Read all posts
            if request.is_xhr:
                posts = Post.query.all()
                return jsonify(myPoems=[i.json_view() for i in posts])
            else:
                view_data = ViewData(page_mark=page_mark)
                return render_template(view_data.template_name, **view_data.context)

        elif slug is not None:       # Read a single post
            detail_data = ViewData(page_mark="detail", slug=slug)
            return render_template(detail_data.template_name, **detail_data.context)

        elif post_id is not None:
            pass  # Todo create logic for xhr request for a single poem

    # Update Post
    def put(self, post_id ):
        form = PostForm()
        if form.validate_on_submit():
            update_post = Post.query.get(post_id)
            update_post.body = form.data['body']
            db.session.commit()
            response = update_post.json_view()
            response['updatedsuccess'] = True
            return json.dumps(response)
        else:
            result = {'updatedsuccess': False}
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
app.add_url_rule('/poetry/<page_mark>', view_func=post_api_view, methods=["POST", "GET"])
# Get, Update or Delete a single post (Restful)
app.add_url_rule('/poetry/portfolio/<int:post_id>', view_func=post_api_view, methods=["GET", "PUT", "DELETE"])
# Read a single post (Non Restful)
app.add_url_rule('/poetry/detail/<slug>', view_func=post_api_view, methods=["GET"])


class FormsAPI(MethodView):
    def post(self, page_mark=None, post_id=None):
        form = CommentForm()
        if request.is_xhr:
            if form.validate_on_submit():
                result = {'iserror': False}
                comment = Comment(created_at=datetime.utcnow(), user_id=g.user.id, body=form.comment.data,
                                  post_id=post_id)
                db.session.add(comment)
                db.session.commit()
                result['savedsuccess'] = True
                result['new_comment'] = render_template('assets/posts/comment.html', comment=comment)
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
                return redirect(url_for('posts', slug=post.slug))
            else:
                post = Post.query.get(post_id)
                detail_data = ViewData(page_mark=page_mark, slug=post.slug, form=form)
                return render_template(detail_data.template_name, **detail_data.context)

    def get(self, page_mark=None, post_id=None):
        if post_id is None:    # Add post form to a page (NoJS)
            view_data = ViewData(page_mark=page_mark, render_form=True)
            return render_template(view_data.template_name, **view_data.context)

        else:  # Delete post (NoJS)
            post = Post.query.get(post_id)
            db.session.delete(post)
            db.session.commit()
            if str(request.referrer).split('/')[-2] != 'detail':
                return redirect(redirect_url())
            else:
                return redirect(url_for('posts', page_mark='portfolio'))

# urls for Forms API
forms_api_view = FormsAPI.as_view('forms')
# Process form for a Comment
app.add_url_rule('/forms/<page_mark>/<int:post_id>', view_func=forms_api_view, methods=["POST"])
# Delete a single post (NoJS)
app.add_url_rule('/forms/<page_mark>/<int:post_id>', view_func=forms_api_view, methods=["GET"])
# Add post form to a page
app.add_url_rule('/forms/<page_mark>/', view_func=forms_api_view, methods=["GET"])


class ActionsAPI(MethodView):
        def post(self, page_mark=None, action=None, post_id=None):
            if action == 'vote':   # Vote on post
                post_id = post_id
                user_id = g.user.id
                if not post_id:
                    abort(404)
                post = Post.query.get_or_404(int(post_id))
                vote_status = post.vote(user_id=user_id)
                return jsonify(new_votes=post.votes, vote_status=vote_status)

        def get(self, page_mark=None, action=None, post_id=None):
            if action == 'vote':   # Vote on post
                post_id = post_id
                user_id = g.user.id
                if not post_id:
                    abort(404)
                post = Post.query.get_or_404(int(post_id))
                post.vote(user_id=user_id)
                return redirect(redirect_url())

actions_api_view = ActionsAPI.as_view('actions')
app.add_url_rule('/actions/<page_mark>/<action>/<int:post_id>', view_func=actions_api_view, methods=["POST", "GET"])


# Helper functions #


def redirect_url(default='home'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


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


@app.template_filter('curly')  # Filter to create curly braces
def curly(value):
    # Handle value as string  {{'foo'|curly}}
    if isinstance(value,str):
        return_value = value
    # Handle value directly. {{foo|curly}}
    else:
        return_value = value._undefined_name
    return "{{" + return_value + "}}"
