from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, SubmitField, PasswordField, SelectField
from flask.ext.wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Email, Length, ValidationError
from .models import User


class LoginForm(Form):
    email = StringField("Email",  [DataRequired("Please enter your email address."), Email("Please enter your email address.")])
    password = PasswordField('Password', [DataRequired("Please enter a password.")])
    remember_me = BooleanField('remember_me', default=False)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(email=self.email.data.lower()).first()
        if user and user.check_password(self.password.data):
            return True
        else:
            self.email.errors.append("Invalid e-mail or password")
            return False


class SignupForm(Form):
    firstname = StringField("First name",  [DataRequired("Please enter your first name.")])
    lastname = StringField("Last name",  [DataRequired("Please enter your last name.")])
    email = StringField("Email",  [DataRequired("Please enter your email address."), Email("Please enter your email address.")])
    password = PasswordField('Password', [DataRequired("Please enter a password.")])
    submit = SubmitField("Create account")
    remember_me = BooleanField('remember_me', default=False)

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

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data != User.make_valid_nickname(self.nickname.data):
            self.nickname.errors.append(
                'This nickname has invalid characters. '
                'Please use letters, numbers, dots and underscores only.')
            return False
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append(
                'This nickname is already in use.')
            return False
        return True


class PostForm(Form):
    my_choices = [('poem', 'Poem'), ('op-ed', 'Op-ed')]
    post = TextAreaField('Post', validators=[DataRequired()])
    header = StringField('Header', validators=[DataRequired()])
    writing_type = SelectField('Post Type', choices=my_choices, default='poem')
    photo = FileField('Your photo', validators=[FileAllowed(['jpg','png'], 'Images only!')])
    submit = SubmitField("Send")


class CommentForm(Form):
    comment = StringField('comment', validators=[DataRequired()])
    submit = SubmitField("Send")
    

class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])


class ContactForm(Form):
    name = StringField("Name")
    email = StringField("Email")
    subject = StringField("Subject")
    message = TextAreaField("Message")
    submit = SubmitField("Send")
