import os
basedir = os.path.abspath(os.path.dirname(__file__))
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, session, url_for, request, g

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


@app.context_processor
def inject_static_url():
    local_static_url = app.static_url_path
    static_url = 'https://s3.amazonaws.com/netbardus/'
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
        return redirect(url_for('portfolio', id=g.user.id))

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
        return redirect(url_for('portfolio', id=g.user.id))

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


@app.route('/', methods=['GET', 'POST'])
@app.route('/home/<int:page>', methods=['GET', 'POST'])
def home(page=1):
    posts_this_page = 1
    page_mark = 'home'
    page_logo = 'img/icons/home.svg'
    super_user = User.query.filter_by(type=1).first()
    op_ed_posts = super_user.all_op_eds().paginate(page, posts_this_page, False)
    return render_template('home.html',
                           title='Home',
                           posts=op_ed_posts,
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/poetry', methods=['GET', 'POST'])
def poetry():
    page_mark = 'poetry'
    page_logo = 'img/icons/poetry.svg'
    return render_template('poetry.html',
                           title='Poetry',
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/workshop', methods=['GET', 'POST'])
@app.route('/workshop/<int:page>', methods=['GET', 'POST'])
@login_required
def workshop(page=1):
    all_posts = g.user.all_poems().paginate(page, POSTS_PER_PAGE, False)
    # favorite_posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    page_mark = 'workshop'
    page_logo = 'img/icons/workshop.svg'
    return render_template('workshop.html',
                           title='Workshop',
                           posts=all_posts,
                           page_mark=page_mark,
                           page_logo=page_logo,
                           upload_folder_name=app.config['UPLOAD_FOLDER_NAME'])


@app.route('/essays', methods=['GET', 'POST'])
def essays():
    page_mark = 'essays'
    page_logo = 'img/icons/essays.svg'
    return render_template('essays.html',
                           title='Essays',
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/portfolio/<int:id>', methods=['GET', 'POST'])
@app.route('/portfolio/<int:id>/<int:page>', methods=['GET', 'POST'])
@login_required
def portfolio(id, page=1):
    portfolio_owner = User.query.get(id)
    if portfolio_owner is None:
        flash('User %(id)s not found.', id=id)
        return redirect(url_for('home'))
    form = PostForm()
    if form.validate_on_submit():
        slug = slugify(form.header.data)
        post = Post(body=form.post.data, timestamp=datetime.utcnow(),
                    author=g.user, photo=None, thumbnail=None, header=form.header.data,
                    writing_type=form.writing_type.data, slug=slug)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(request.args.get('next') or url_for('user', nickname=g.user.nickname))
    portfolio_owner_posts = portfolio_owner.posts.paginate(page, POSTS_PER_PAGE, False)
    page_mark = 'portfolio'
    page_logo = 'img/icons/portfolio.svg'
    return render_template('portfolio.html',
                           form=form,
                           posts=portfolio_owner_posts,
                           title='Portfolio',
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
def user(id):
    present_user = User.query.get(id)
    if present_user is None:
        flash('User %(id)s not found.' % id)
        return redirect(url_for('home'))
    page_mark = 'profile'
    page_logo = 'img/icons/profile.svg'
    return render_template('user.html',
                           user=present_user,
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route('/edit', methods=['GET', 'POST'])
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
        return redirect(url_for('user', id=g.user.id))
    elif request.method != "POST":
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    page_mark = 'profile'
    page_logo = 'img/icons/profile.svg'
    return render_template('edit.html',
                           form=form,
                           page_mark=page_mark,
                           page_logo=page_logo)


@app.route("/detail/<slug>", methods=['GET', 'POST'])
def posts(slug):
    post = Post.query.filter(Post.slug == slug).first()
    form = CommentForm()
    context = {"post": post, "form": form}
    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, created_at=datetime.utcnow(), user_id=g.user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('posts', slug=slug))
    page_mark = 'post_detail'
    page_logo = 'img/icons/workshop.svg'
    return render_template('post_detail.html',
                           page_mark=page_mark,
                           page_logo=page_logo,
                           **context)


@app.route('/edit_in_place', methods=['POST'])
def edit_in_place():
    update_post = Post.query.get(request.form['post_id'])
    update_post.body = request.form['content']
    # update_post.header=request.form['header']
    db.session.commit()
    return request.form['content']


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('home'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow %s.' % nickname)
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following %s.' % nickname)
    follower_notification(user, g.user)
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('home'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow %s.' % nickname)
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following %s.' % nickname)
    return redirect(url_for('user', nickname=nickname))


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post not found.')
        return redirect(url_for('home'))
    if post.author.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('home'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.')
    return redirect(url_for('portfolio', id=post.author.id))


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
    username, email = oauth.callback()
    if email is None:
        flash('Authentication failed.')
        return redirect(url_for('home'))
    currentuser = User.query.filter_by(email=email).first()
    if not currentuser:
        currentuser = User(nickname=username, email=email)
        db.session.add(currentuser)
        db.session.add(currentuser.follow(currentuser))
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(currentuser, remember=remember_me)
    return redirect(request.args.get('next') or url_for('portfolio', id=currentuser.id))
