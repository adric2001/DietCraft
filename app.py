import os
from requests import get
from dotenv import load_dotenv
from modules.dietcraft import DietCraft
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from modules.forms import RegisterForm, LoginForm, SettingsForm, CustomMealForm

# Load environment variables from .env file
load_dotenv()
spoonacular_api_key = os.getenv("SPOONACULAR_API_KEY")
secret_key = os.getenv("SECRET_KEY")

# Define absolute path for the database
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'data', 'diet.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure 'data' folder exists

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secrets123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

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

    #Requirements
    calorie_requirement: Mapped[int] = mapped_column(Integer, nullable=True)
    protein_requirement: Mapped[int] = mapped_column(Integer, nullable=True)

     # Relationship to MealPlan
    meal_plans: Mapped[list["MealPlan"]] = relationship("MealPlan", back_populates="user")

class MealPlan(db.Model):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    day: Mapped[str] = mapped_column(String(20))  # e.g., "Day 1", "Day 2"
    meal_type: Mapped[str] = mapped_column(String(20))  # e.g., "breakfast", "lunch"
    title: Mapped[str] = mapped_column(String(255))
    calories: Mapped[int] = mapped_column(Integer)
    protein: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(String(255), nullable=True)
    custom_meal_title: Mapped[str] = mapped_column(String(255), nullable=True)
    custome_meal_calories: Mapped[int] = mapped_column(Integer, nullable=True)
    custom_meal_protein: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationship back to User
    user: Mapped["User"] = relationship("User", back_populates="meal_plans")


with app.app_context():
    db.create_all()


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
        return redirect(url_for("profile"))
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
            return redirect(url_for('profile'))

    return render_template("login.html", form=form, current_user=current_user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = SettingsForm()

    # Initialize variables to avoid UnboundLocalError
    calorie_requirement = None
    protein_requirement = None

    if request.method == 'GET':
        # Pre-fill form with the user's current settings
        form.age.data = current_user.age
        form.gender.data = current_user.gender
        form.height_feet.data = current_user.height_feet
        form.height_inches.data = current_user.height_inches or 0
        form.desired_weight.data = current_user.desired_weight
        form.current_weight.data = current_user.current_weight
        form.activity_level.data = current_user.activity_level
        form.time_frame.data = current_user.time_frame
        form.goal.data = current_user.goal

        # Calculate requirements for the initial GET request (optional)
        if current_user.age and current_user.current_weight:
            calorie_requirement = DietCraft.generate_calorie_requirements(
                age=current_user.age,
                gender=current_user.gender,
                height_feet=current_user.height_feet,
                height_inch=current_user.height_inches or 0,
                weight=current_user.current_weight,
                desired_weight=current_user.desired_weight,
                time_frame=current_user.time_frame,
                activity=current_user.activity_level,
            )

            protein_requirement = DietCraft.generate_protein_requirements(
                goal=current_user.goal,
                weight=current_user.current_weight,
            )

         # Get meals for the current user
        meals = MealPlan.query.filter_by(user_id=current_user.id).all()

    if form.validate_on_submit():
        # Update user settings in the database
        current_user.age = form.age.data
        current_user.gender = form.gender.data
        current_user.height_feet = form.height_feet.data
        current_user.height_inches = form.height_inches.data if form.height_inches.data is not None else 0
        current_user.desired_weight = form.desired_weight.data
        current_user.current_weight = form.current_weight.data
        current_user.activity_level = form.activity_level.data
        current_user.time_frame = form.time_frame.data
        current_user.goal = form.goal.data

        # Recalculate requirements after the form submission
        calorie_requirement = DietCraft.generate_calorie_requirements(
            age=current_user.age,
            gender=current_user.gender,
            height_feet=current_user.height_feet,
            height_inch=current_user.height_inches or 0,
            weight=current_user.current_weight,
            desired_weight=current_user.desired_weight,
            time_frame=current_user.time_frame,
            activity=current_user.activity_level,
        )

        protein_requirement = DietCraft.generate_protein_requirements(
            goal=current_user.goal,
            weight=current_user.current_weight,
        )

        # Save calorie and protein requirements to the database
        current_user.calorie_requirement = calorie_requirement
        current_user.protein_requirement = protein_requirement

        if calorie_requirement == "Not Suggested":
            flash("Your Settings have not been Updated!")
            pass
        else:
            flash("Your Settings have been Updated!")
            db.session.commit()  

        return redirect(url_for('profile'))  # Redirect to refresh the page with saved data

    return render_template(
        "profile.html",
        current_user=current_user,
        form=form,
        calorie_requirement=calorie_requirement,
        protein_requirement=protein_requirement,
        meals=meals,
    )

@app.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    form = CustomMealForm()

    if request.method == 'GET':
        form.title = current_user.custom_title
        form.calories = current_user.custom_calories
        form.protein = current_user.custom_protein
    
    if form.validate_on_submit():
        current_user.custom_title = form.title
        current_user.custom_calories = form.calories
        current_user.custom_protein = form.process

    return redirect(url_for('profile'))  # Redirect to refresh the page with saved data


@app.route('/generate', methods=['GET'])
@login_required
def generate_meals():
    if (
        current_user.calorie_requirement is not None
        and current_user.protein_requirement is not None
        and current_user.goal is not None
    ):
        try:
            # Ensure calorie and protein requirements are numeric
            daily_calories = float(current_user.calorie_requirement)
            daily_protein = float(current_user.protein_requirement)

            # Delete existing meal plans for the current user
            MealPlan.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()  # Commit the deletion to ensure a clean slate

            # Call the function to generate meals
            result = DietCraft.generate_weekly_meals(
                api_key=spoonacular_api_key,
                daily_calories=daily_calories,
                daily_protein=daily_protein,
                goal=current_user.goal,
            )

            # Store the result in the MealPlan table
            for day, daily_meals in result.items():
                for meal_type, details in daily_meals.items():
                    meal_plan = MealPlan(
                        user_id=current_user.id,
                        day=day,
                        meal_type=meal_type,
                        title=details["title"],
                        calories=details["calories"],
                        protein=details["protein"],
                        url=details["url"],
                    )
                    db.session.add(meal_plan)

            db.session.commit()  # Commit the new meal plan to the database

            flash("Meals Generated and Saved")
            return redirect(url_for('profile'))

        except ValueError:
            flash("Error: Invalid calorie or protein requirement.")
            return redirect(url_for('profile'))
    else:
        flash("Error: Some required fields are missing.")
        return redirect(url_for('profile'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
