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
from modules.forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Retrieve the API key from .env
api_key = os.getenv('API_KEY')

# Create an instance of DietCraft with the API key
dietcraft = DietCraft(api_key)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diet.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))

    

with app.app_context():
    db.create_all()

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
    if request.method == 'POST':
        try:
            # Get form data
            age = int(request.form['age'])
            gender = request.form['gender']
            height_feet = int(request.form['height_feet'])
            height_inches = int(request.form['height_inches'])
            desired_weight = int(request.form['desired_weight'])
            current_weight = int(request.form['current_weight'])
            activity_level = request.form['activity_level']
            time_frame = int(request.form['time_frame'])
            goal = request.form['goal']
            
            # Update user object
            current_user.age = age
            current_user.gender = gender
            current_user.height_feet = height_feet
            current_user.height_inches = height_inches
            current_user.desired_weight = desired_weight
            current_user.current_weight = current_weight
            current_user.activity_level = activity_level
            current_user.time_frame = time_frame
            current_user.goal = goal

            # Save to database
            db.session.commit()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')

        return redirect(url_for('settings'))
    
    # Render the settings form with current user data
    return render_template('settings.html', user=current_user)

@app.route('/')
def home():
    return render_template('index.html', current_user=current_user)


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
