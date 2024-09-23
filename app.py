from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
from modules.dietcraft import DietCraft

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Retrieve the API key from .env
api_key = os.getenv('API_KEY')

# Create an instance of DietCraft with the API key
dietcraft = DietCraft(api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    # Get data from form
    age = int(request.form['age'])
    gender = request.form['gender']
    height_feet = int(request.form['height_feet'])
    height_inches = int(request.form['height_inches'])
    desired_weight = int(request.form['desired_weight'])
    current_weight = int(request.form['current_weight'])
    activity_level = request.form['activity_level']
    time_frame = int(request.form['time_frame'])
    goal = request.form['goal']

    print(age, gender, height_feet, height_inches, desired_weight, current_weight, activity_level, time_frame, goal)

    # Calculate calories and protein requirements using the DietCraft instance
    calories = dietcraft.generate_calorie_requirements(age, gender, height_feet, height_inches, current_weight, desired_weight, time_frame, activity_level)
    protein = dietcraft.generate_protein_requirements(goal, current_weight)

    # Generate diet plan using the DietCraft instance
    weekly_diet_plan_df = dietcraft.generate_weekly_diet_plan(calories, protein)

    return render_template('result.html', calories=calories, protein=protein, diet_plan=weekly_diet_plan_df.to_html())

if __name__ == "__main__":
    app.run(debug=True)
