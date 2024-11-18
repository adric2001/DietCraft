import requests
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

def generate_weekly_meals(api_key, daily_calories, daily_protein):
    # Define meal calorie and protein distribution
    meal_distribution = {
        "breakfast": 0.25,  # 25% of daily calories
        "lunch": 0.35,      # 35% of daily calories
        "dinner": 0.30,     # 30% of daily calories
        "snack": 0.10       # 10% of daily calories
    }

    # Define meal types
    meal_types = {
        "breakfast": ["breakfast"],
        "lunch": ["main course", "salad", "soup"],
        "dinner": ["main course", "side dish"],
        "snack": ["snack", "fingerfood", "dessert"]
    }

    # Calculate calories and protein for each meal
    meal_requirements = {
        meal: {
            "calories": int(daily_calories * fraction),
            "protein": int(daily_protein * fraction),
            "type": meal_types[meal]
        }
        for meal, fraction in meal_distribution.items()
    }

    # Track recipe usage
    recipe_usage = defaultdict(int)  # Key: recipe ID, Value: count

    # Function to call the Spoonacular API
    def fetch_recipe(calories, protein, types):
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "number": 10,  # Fetch multiple recipes to choose from
            "maxCalories": calories + 50,  # Allow a small buffer
            "minProtein": protein - 5,     # Slightly relaxed protein requirement
            "type": ",".join(types),       # Specify the meal types
            "addRecipeNutrition": True,    # Include nutrition details
            "apiKey": api_key              # Include API key in parameters
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Filter recipes based on usage criteria
            recipes = data.get("results", [])
            for recipe in recipes:
                recipe_id = recipe["id"]
                if recipe_usage[recipe_id] < 2:  # Limit usage to twice per week
                    recipe_usage[recipe_id] += 1
                    return recipe
            print(f"No suitable recipes found for {types} with {calories} kcal and {protein}g protein.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"API connection error: {e}")
            return None

    # Generate a week's worth of meals
    weekly_meals = {}
    for day in range(1, 8):  # Loop through 7 days
        daily_plan = {}
        used_recipes_today = set()  # Track recipes used for the current day
        for meal, requirements in meal_requirements.items():
            while True:
                recipe = fetch_recipe(
                    requirements["calories"], 
                    requirements["protein"], 
                    requirements["type"]
                )
                if recipe and recipe["id"] not in used_recipes_today:
                    used_recipes_today.add(recipe["id"])  # Mark recipe as used today
                    daily_plan[meal] = {
                        "title": recipe["title"],
                        "calories": recipe["nutrition"]["nutrients"][0]["amount"],  # Calories
                        "protein": recipe["nutrition"]["nutrients"][1]["amount"],  # Protein
                        "url": f'https://spoonacular.com/recipes/{recipe["title"].replace(" ", "-")}-{recipe["id"]}'
                    }
                    break
                elif not recipe:
                    # If no recipe is found, fallback to a placeholder
                    daily_plan[meal] = {
                        "title": "No recipe found",
                        "calories": 0,
                        "protein": 0,
                        "url": None
                    }
                    break
        weekly_meals[f"Day {day}"] = daily_plan

    return weekly_meals

# Example usage
api_key = os.getenv("SPOONACULAR_API_KEY")
if not api_key:
    print("Error: SPOONACULAR_API_KEY is not set in the .env file.")
else:
    daily_calories = 2000
    daily_protein = 120

    weekly_meals = generate_weekly_meals(api_key, daily_calories, daily_protein)

    # Print the meal plan
    for day, meals in weekly_meals.items():
        print(day)
        for meal, details in meals.items():
            print(f"  {meal.title()}: {details['title']} ({details['calories']} kcal, {details['protein']}g protein)")
            print(f"    URL: {details['url']}")
        print()
