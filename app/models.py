from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
import re
from app import db
from app import app
from config import WHOOSH_ENABLED
from flask import url_for
from flask.ext.login import UserMixin

import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = WHOOSH_ENABLED
    if enable_search:
        import flask.ext.whooshalchemy as whooshalchemy


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    pwdhash = db.Column(db.String(100))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    profile_photo = db.Column(db.String(240))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    def __init__(self, nickname, email, password=None, firstname=None, lastname=None):
        self.nickname = nickname
        self.email = email.lower()
        if password is not None:
            self.set_password(password)
        if firstname is not None:
            self.firstname = firstname.title()
        if lastname is not None:
            self.lastname = lastname.title()


    def set_password(self, password):
        self.pwdhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)

    @staticmethod
    def make_valid_nickname(nickname):
        return re.sub('[^a-zA-Z0-9_\.]', '', nickname)

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname


    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
            (md5(self.email.encode('utf-8')).hexdigest(), size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def all_posts(self):
        return Post.query.order_by(Post.timestamp.desc())

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).order_by(
                    Post.timestamp.desc())

    def __repr__(self):  # pragma: no cover
        return '<User %r>' % self.nickname


class Post(db.Model):
    __searchable__ = ['body']
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.String(140))
    body = db.Column(db.Text())
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))
    photo = db.Column(db.String(240))
    thumbnail = db.Column(db.String(240))
    comments = db.relationship('Comment', backref='original_post', lazy='dynamic')
    slug = db.Column(db.String(255))

    def get_absolute_url(self):
        return url_for('post', kwargs={"slug": self.slug})

    def __repr__(self):  # pragma: no cover
        return '<Post %r>' % (self.body)


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(500))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime)

    def __repr__(self):  # pragma: no cover
        return '<Comment %r>' % self.body

if enable_search:
    whooshalchemy.whoosh_index(app, Post)


