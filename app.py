from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABSE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "666"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)
toolbar = DebugToolbarExtension(app)


@app.route('/')
def homepage():
	"""Redirect to registeration page."""

	return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def show_form():
	"""Show form to register a user"""
	if "username" in session:
 	       return redirect(f"/users/{session['username']}")

	form = RegisterForm()

	if form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		first_name = form.first_name.data
		last_name = form.last_name.data
		email = form.email.data

		user = User.register(username, password, first_name, last_name, email)

		db.session.commit()
		session['username'] = user.username

		return redirect(f"/users/{user.username}")
	else:
		return render_template("users/register.html", form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
	"""Show login form and handle login."""
	if "username" in session:
		return redirect(f"/users/{session['username']}")

	form = LoginForm()
	
	if form.validate_on_submit():
		username= form.username.data
		password = form.password.data
		
		user = User.authenticate(username, password)
		if user:
			session['username'] = user.username
			return redirect(f"/users/{user.username}")
		else:
			form.username.errors = ["Invalid username/password."]
			return render_template("users/login.html", form=form)

	return render_template("users/login.html", form=form)



@app.route('/logout')
def logout():
	"""Logout route"""
	session.pop("username")
	return redirect("/login")



@app.route('/users/<username>')
def show_user(username):
	"""Show user page for logged in users"""

	if "username" not in session or username != session['username']:
		raise Unauthorized()

	user = User.query.get(username)
	
	form = DeleteForm()

	return render_template("users/show.html", user=user, form=form)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
	"""Remove user and redirect to login"""

	if "username" not in session or username != session['username']:
		raise Unauthorized
	
	user = User.query.get(username)
	db.session.delete(user)
	db.session.commit()
	session.pop("username")

	return redirect('/login')


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
	"""Add new feedback from the user"""

	if "username" not in session or username != session['username']:
		raise Unauthorized()

	form = FeedbackForm()

	if form.validate_on_submit():
		title = form.title.data
		content = form.content.data

		feedback = Feedback(title = title, content=content, username= username)
		db.session.add(feedback)
		db.session.commit()

		return redirect(f"/users/{feedback.username}")
	else:
		return render_template("feedback/new.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
	"""Show update-feedback form and process it"""

	feedback = Feedback.query.get(feedback_id)

	if "username" not in session or feedback.username != session['username']:
		raise Unauthorized()

	form = FeedbackForm(obj=feedback)

	if form.validate_on_submit():
		feedback.title = form.title.data
		feedback.content = form.content.data

		db.session.commit()

		return redirect(f"/users/{feedback.username}")
	return render_template("/feedback/edit.html", form=form, feedback=feedback)



@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
	"""Delete Feedback"""

	feedback = Feedback.query.get(feedback_id)
	if "username" not in session and feedback.username != session['username']:
		raise Unauthorized()
	
	form = DeleteForm()

	if form.validate_on_submit():
		db.session.delete(feedback)
		db.session.commit()
	
	return redirect(f"/users/{feedback.username}")



