from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo


class SupportTicketForm(FlaskForm):
    action = HiddenField(default="create")
    subject = StringField("Subject", validators=[DataRequired(), Length(min=3, max=100)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=5)])
    submit = SubmitField("Send Query")


class ProfileForm(FlaskForm):
    username = StringField("Username", render_kw={"readonly": True})
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full Name", validators=[DataRequired()])
    enrollment_number = StringField("Enrollment Number", validators=[DataRequired()])
    course = SelectField(
        "Course",
        choices=[
            ("B.Tech", "B.Tech"),
            ("M.Tech", "M.Tech"),
            ("MCA", "MCA"),
            ("BCA", "BCA"),
        ],
        validators=[DataRequired()],
    )
    semester = SelectField("Semester", choices=[(str(i), f"Semester {i}") for i in range(1, 9)], validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[Optional(), Length(min=6, message="Password must be at least 6 characters")])
    submit = SubmitField("Save Changes")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    full_name = StringField("Full Name", validators=[DataRequired()])
    course = SelectField("Course", choices=[("B.Tech", "B.Tech"), ("M.Tech", "M.Tech"), ("BCA", "BCA"), ("MCA", "MCA")], validators=[DataRequired()])
    semester = SelectField("Semester", choices=[(str(i), f"Semester {i}") for i in range(1, 9)], validators=[DataRequired()])
    enrollment_number = StringField("Enrollment Number", validators=[DataRequired()])
    submit = SubmitField("Register")
