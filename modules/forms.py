from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, SelectField
from wtforms.validators import DataRequired, Optional


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!", render_kw={'class': 'btn-hover btn-warning'})

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!", render_kw={'class': 'btn-hover btn-warning'})

class SettingsForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    height_feet = IntegerField('Height (feet)', validators=[DataRequired()])
    height_inches = IntegerField('Height (inches)', validators=[Optional()])
    desired_weight = IntegerField('Desired Weight', validators=[DataRequired()])
    current_weight = IntegerField('Current Weight', validators=[DataRequired()])
    activity_level = SelectField('Activity Level', choices=[('sedentary', 'Sedentary'), 
                                                            ('light', 'Light'), 
                                                            ('moderate', 'Moderate'), 
                                                            ('active', 'Active')], 
                                validators=[DataRequired()])
    time_frame = IntegerField('Time Frame (in weeks)', validators=[DataRequired()])
    goal = SelectField('Focus', choices=['Gain Muscle', 'Maintain Muscle'], validators=[DataRequired()])