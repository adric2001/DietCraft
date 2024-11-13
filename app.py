from dotenv import load_dotenv
import os
from modules.dietcraft import DietCraft
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, session, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
# Import your forms from the forms.py
from modules.forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, SettingsForm

# Load environment variables from .env file
# load_dotenv() ** Not Being Used at the moment

# Define absolute path for the database
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'data', 'diet.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure 'data' folder exists

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))

     # Settings fields
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=True)
    height_feet: Mapped[int] = mapped_column(Integer, nullable=True)
    height_inches: Mapped[int] = mapped_column(Integer, nullable=True)
    desired_weight: Mapped[int] = mapped_column(Integer, nullable=True)
    current_weight: Mapped[int] = mapped_column(Integer, nullable=True)
    activity_level: Mapped[str] = mapped_column(String(20), nullable=True)
    time_frame: Mapped[int] = mapped_column(Integer, nullable=True)
    goal: Mapped[str] = mapped_column(String(255), nullable=True)


with app.app_context():
    db.drop_all()    # Drops all tables
    db.create_all()

ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Retrieve the API key from .env
# api_key = os.getenv('API_KEY') Fix data stuff

# Create an instance of DietCraft with the API key
# dietcraft = DietCraft(api_key) Fix data stuff

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/question1')
def question_1():
    return render_template('question_1.html')

# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

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
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()

    if request.method == 'GET':
        # Pre-fill form with the user's current settings
        form.age.data = current_user.age
        form.gender.data = current_user.gender
        form.height_feet.data = current_user.height_feet
        form.height_inches.data = current_user.height_inches
        form.desired_weight.data = current_user.desired_weight
        form.current_weight.data = current_user.current_weight
        form.activity_level.data = current_user.activity_level
        form.time_frame.data = current_user.time_frame
        form.goal.data = current_user.goal

    if form.validate_on_submit():
        # Update user settings in the database
        current_user.age = form.age.data
        current_user.gender = form.gender.data
        current_user.height_feet = form.height_feet.data
        current_user.height_inches = form.height_inches.data
        current_user.desired_weight = form.desired_weight.data
        current_user.current_weight = form.current_weight.data
        current_user.activity_level = form.activity_level.data
        current_user.time_frame = form.time_frame.data
        current_user.goal = form.goal.data
        
        db.session.commit()  # Save changes to the database
        return redirect(url_for('home'))  # Redirect to refresh the page with saved data

    return render_template('settings.html', form=form)



# @app.route('/form')
# def form():
#     return render_template('form.html')

# @app.route('/calculate', methods=['POST'])
# def calculate():
#     # Get data from form
#     age = int(request.form['age'])
#     gender = request.form['gender']
#     height_feet = int(request.form['height_feet'])
#     height_inches = int(request.form['height_inches'])
#     desired_weight = int(request.form['desired_weight'])
#     current_weight = int(request.form['current_weight'])
#     activity_level = request.form['activity_level']
#     time_frame = int(request.form['time_frame'])
#     goal = request.form['goal']

#     print(age, gender, height_feet, height_inches, desired_weight, current_weight, activity_level, time_frame, goal)

#     # Calculate calories and protein requirements using the DietCraft instance
#     calories = dietcraft.generate_calorie_requirements(age, gender, height_feet, height_inches, current_weight, desired_weight, time_frame, activity_level)
#     protein = dietcraft.generate_protein_requirements(goal, current_weight)

#     # Generate diet plan using the DietCraft instance
#     weekly_diet_plan_df = dietcraft.generate_weekly_diet_plan(calories, protein)

#     return render_template('result.html', calories=calories, protein=protein, diet_plan=weekly_diet_plan_df.to_html())

if __name__ == "__main__":
    app.run(debug=True)
