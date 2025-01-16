from datetime import date, datetime
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, CreateTaskForm
import smtplib
# from flask_migrate import Migrate


EMAIL = 'reenoxgooglov@gmail.com'
PASSWORD = 'mzbwcvsdbsyhahms'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

    # *******Add parent relationship******* #
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")


class Task(db.Model):
    __tablename__ = "tasks"
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(250), nullable=False)
    description = mapped_column(Text, nullable=True)
    due_date = mapped_column(String(250), nullable=False)
    priority = mapped_column(String(50), nullable=False)
    completed = mapped_column(db.Boolean, default=False)
    completed_date = mapped_column(String(250), nullable=True)
    creator_id = mapped_column(Integer, db.ForeignKey("users.id"))
    creator = relationship("User", back_populates="tasks")

# Update the User model
User.tasks = relationship("Task", back_populates="creator")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. the "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post", cascade="all, delete-orphan")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # *******Add child relationship*******#
    # "users.id" The users refers to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # ***************Child Relationship*************#
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text: Mapped[str] = mapped_column(Text, nullable=False)


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


# Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        # If the email doesn't exist, proceed with user registration
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, current_user=current_user)


# Retrieve a user from the database based on their email.
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        elif not user:
            flash("That email does not exist, please try again!")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again!")
            return redirect(url_for('login'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/tasks")
def get_tasks():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(creator_id=current_user.id, completed=False).all()
    return render_template("tasks.html", tasks=tasks, current_user=current_user)


@app.route("/task/new", methods=["GET", "POST"])
def new_task():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = CreateTaskForm()
    if form.validate_on_submit():
        new_task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            completed=False,
            creator=current_user
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("get_tasks"))
    return render_template("create_task.html", form=form, current_user=current_user)


@app.route("/task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = db.get_or_404(Task, task_id)
    if task.creator_id != current_user.id:
        abort(403)
    form = CreateTaskForm(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority
    )
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.due_date = form.due_date.data
        task.priority = form.priority.data
        db.session.commit()
        return redirect(url_for("get_tasks"))
    return render_template("create_task.html", form=form, current_user=current_user, is_edit=True)


@app.route("/task/delete/<int:task_id>")
def delete_task(task_id):
    task_to_delete = db.get_or_404(Task, task_id)
    if task_to_delete.creator_id != current_user.id:
        abort(403)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("get_tasks"))


@app.route("/task/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    task = db.get_or_404(Task, task_id)
    if task.creator_id != current_user.id:
        abort(403)
    task.completed = True
    task.completed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.session.commit()
    return redirect(url_for("get_tasks"))


@app.route("/tasks/history")
def completed_tasks():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    completed = Task.query.filter_by(creator_id=current_user.id, completed=True).all()
    return render_template("completed_tasks.html", tasks=completed, current_user=current_user)


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # Add the CommentForm to the route
    comment_form = CommentForm()
    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author =current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


# Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


# Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


# Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


@app.route("/contact", methods=['GET', 'POST'])
def receive_data():
    if request.method == "POST":
        data = request.form
        send_email(data['name'], data['email'], data['phone'], data['message'])
        return render_template('contact.html', message="Successfully sent your message")
    else:
        return render_template('contact.html')


def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(EMAIL, PASSWORD)
        connection.sendmail(EMAIL, "aladdinjakubowski@gmail.com", email_message)


# migrate = Migrate(app, db)


if __name__ == "__main__":
    app.run(debug=False, port=5002)


