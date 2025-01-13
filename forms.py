from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.choices import SelectField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

class CreateTaskForm(FlaskForm):
    title = StringField("Task Title", validators=[DataRequired()])
    description = CKEditorField("Task Description")
    due_date = StringField("Due Date (YYYY-MM-DD)", validators=[DataRequired()])
    priority = SelectField(
        "Priority",
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Task")


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


# Create a CommentForm to comment
class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")