from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.forms import LoginForm, RegisterForm
from database.models import ActivityLog, User
from utils.logger import setup_logger


auth_bp = Blueprint("auth", __name__)

# Create module-specific logger
logger = setup_logger("app.auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            logger.info("User Logged In")
            return redirect(url_for("routes.dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        full_name = form.full_name.data
        course = form.course.data
        semester = form.semester.data
        enrollment_number = form.enrollment_number.data

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect(url_for("auth.register"))

        new_user = User(username=username, email=email, password=generate_password_hash(password), full_name=full_name, course=course, semester=semester, enrollment_number=enrollment_number)

        try:
            db.session.add(new_user)
            db.session.commit()
            logger.info("New User Register")
            flash("Registration successful! Please login.", "success")
            activity_log = ActivityLog(user_id=User.query.filter_by(username=username).first().id, action="Profile Created", icon="bi bi-person-check", description="You created a new profile")
            print(activity_log)
            try:
                db.session.add(activity_log)
                db.session.commit()
            except Exception as e:
                logger.exception(f"Error Acitvity Logging: {e}")
                db.session.rollback()
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error Regestering User: {e}")
            logger.error("Error during registration, Please try again")
            flash("Error during registration. Please try again.", "error")

    return render_template("register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    logger.info("User Logged Out")
    return redirect(url_for("auth.login"))
