from flask.ext.wtf import Form
from flask.ext.babel import gettext
from wtforms import StringField, BooleanField, TextAreaField, SubmitField, PasswordField
from flask.ext.wtf.file import FileField, FileRequired, FileAllowed
from wtforms import validators
from wtforms.validators import DataRequired, Length, ValidationError
from .models import User

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class SignupForm(Form):
  firstname = StringField("First name",  [validators.DataRequired("Please enter your first name.")])
  lastname = StringField("Last name",  [validators.DataRequired("Please enter your last name.")])
  email = StringField("Email",  [validators.DataRequired("Please enter your email address."), validators.Email("Please enter your email address.")])
  password = PasswordField('Password', [validators.DataRequired("Please enter a password.")])
  submit = SubmitField("Create account")

  def __init__(self, *args, **kwargs):
    Form.__init__(self, *args, **kwargs)

  def validate(self):
    if not Form.validate(self):
      return False

    user = User.query.filter_by(email = self.email.data.lower()).first()
    if user:
      self.email.errors.append("That email is already taken")
      return False
    else:
      return True

class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])
    profile_photo = FileField('Your photo', validators=[FileAllowed(['jpg','png'], 'Images only!')])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        if self.nickname.data != User.make_valid_nickname(self.nickname.data):
            self.nickname.errors.append(gettext(
                'This nickname has invalid characters. '
                'Please use letters, numbers, dots and underscores only.'))
            return False
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append(gettext(
                'This nickname is already in use. '
                'Please choose another one.'))
            return False
        return True


class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])
    header = StringField('header', validators=[DataRequired()])
    photo = FileField('Your photo', validators=[FileAllowed(['jpg','png'], 'Images only!')])
    submit = SubmitField("Send")
    
class CommentForm(Form):
    comment = StringField('comment', validators=[DataRequired()])
    submit = SubmitField("Send")
    

class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])
