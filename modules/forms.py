from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, SelectField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


# Create a form to add comments
class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

class SettingsForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    height_feet = IntegerField('Height (feet)', validators=[DataRequired()])
    height_inches = IntegerField('Height (inches)', validators=[DataRequired()])
    desired_weight = IntegerField('Desired Weight', validators=[DataRequired()])
    current_weight = IntegerField('Current Weight', validators=[DataRequired()])
    activity_level = SelectField('Activity Level', choices=[('sedentary', 'Sedentary'), 
                                                            ('light', 'Light'), 
                                                            ('moderate', 'Moderate'), 
                                                            ('active', 'Active')], 
                                validators=[DataRequired()])
    time_frame = IntegerField('Time Frame (in weeks)', validators=[DataRequired()])
    goal = StringField('Goal', validators=[DataRequired()])