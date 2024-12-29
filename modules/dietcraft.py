# modules/dietcraft.py
import pandas as pd
from collections import defaultdict
from io import StringIO
import csv
import requests
from bs4 import BeautifulSoup

class DietCraft:
    def __init__(self):
        pass

    def generate_weekly_meals(api_key, daily_calories, daily_protein, goal="maintain", custom_snack=None):
        """
        Generates weekly meals based on calorie and protein requirements.
        Replaces the snack with a custom meal for every day.

        :param api_key: Spoonacular API key
        :param daily_calories: Daily calorie target
        :param daily_protein: Daily protein target
        :param goal: Weight goal - 'gain', 'lose', or 'maintain'
        :param custom_snack: Dictionary specifying custom meal details to replace snack.
                            Example: {"title": "Fruit Smoothie", "calories": 150, "protein": 5, "url": None}
        :return: Dictionary containing the weekly meal plan
        """
        # Default custom snack if none is provided
        custom_snack = custom_snack or {"title": "Protein Shake (Custom)", "calories": 290, "protein": 33, "url": None}
        snack_calories = custom_snack.get("calories", 0)
        snack_protein = custom_snack.get("protein", 0)

        # Remaining calorie and protein allowance after custom snack
        remaining_calories = max(0, daily_calories - snack_calories)
        remaining_protein = max(0, daily_protein - snack_protein)

        # Define meal calorie and protein distribution
        meal_distribution = {
            "breakfast": 0.25,  # 25% of remaining calories
            "lunch": 0.35,       # 50% of remaining calories
            "dinner": 0.35      # 25% of remaining calories
        }

        # Define meal types
        meal_types = {
            "breakfast": ["breakfast"],
            "lunch": ["main course", "salad", "soup"],
            "dinner": ["main course", "side dish"]
        }

        # Calculate calories and protein for each meal
        meal_requirements = {
            meal: {
                "calories": int(remaining_calories * fraction),
                "protein": int(remaining_protein * fraction),
                "type": meal_types[meal]
            }
            for meal, fraction in meal_distribution.items()
        }

        # Adjust calorie range based on the goal
        def adjust_calorie_range(calories, goal):
            if goal == "Gain":
                return calories, calories + 100  # Prefer equal or slightly over
            elif goal == "Lose":
                return calories - 100, calories  # Prefer equal or slightly under
            return calories - 50, calories + 50  # Balanced range for maintenance

        # Fetch a batch of recipes for each meal type
        def fetch_recipes(meal, min_calories, max_calories, protein, types):
            url = "https://api.spoonacular.com/recipes/complexSearch"
            params = {
                "number": 100,  # Fetch a large batch for reuse
                "minCalories": min_calories,
                "maxCalories": max_calories,
                "minProtein": protein - 5,     # Slightly relaxed protein requirement
                "type": ",".join(types),       # Specify the meal types
                "addRecipeNutrition": True,    # Include nutrition details
                "apiKey": api_key              # Include API key in parameters
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except requests.exceptions.RequestException as e:
                print(f"API connection error for {meal}: {e}")
                return []

        # Pre-fetch recipes for each meal type
        all_recipes = {}
        for meal, req in meal_requirements.items():
            min_cal, max_cal = adjust_calorie_range(req["calories"], goal)
            all_recipes[meal] = fetch_recipes(meal, min_cal, max_cal, req["protein"], req["type"])

        # Track recipe usage
        recipe_usage = defaultdict(int)  # Key: recipe ID, Value: count

        # Generate a week's worth of meals
        weekly_meals = {}
        for day in range(1, 8):  # Loop through 7 days
            daily_plan = {}

            # Add custom snack for each day
            daily_plan["snack"] = {
                "title": custom_snack.get("title", "Custom Snack"),
                "calories": snack_calories,
                "protein": snack_protein,
                "url": custom_snack.get("url", None)
            }

            used_recipes_today = set()  # Track recipes used for the current day
            for meal, recipes in all_recipes.items():
                recipe = next(
                    (r for r in recipes if recipe_usage[r["id"]] < 4 and r["id"] not in used_recipes_today),
                    None
                )
                if recipe:
                    recipe_usage[recipe["id"]] += 1
                    used_recipes_today.add(recipe["id"])
                    
                    # Parse nutritional information
                    nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                    calories_value = next((n["amount"] for n in nutrients if n["name"] == "Calories"), 0)
                    protein_value = next((n["amount"] for n in nutrients if n["name"] == "Protein"), 0)

                    daily_plan[meal] = {
                        "title": recipe["title"],
                        "calories": calories_value,
                        "protein": protein_value,
                        "url": f'https://spoonacular.com/recipes/{recipe["title"].replace(" ", "-")}-{recipe["id"]}'
                    }
                else:
                    daily_plan[meal] = {
                        "title": "No recipe found",
                        "calories": 0,
                        "protein": 0,
                        "url": None
                    }
            weekly_meals[f"Day {day}"] = daily_plan

        return weekly_meals


    def generate_calorie_requirements(age, gender, height_feet, height_inch, weight, desired_weight, time_frame, activity):
        if activity == 'light':
            activity = 1.375
        elif activity == 'moderate':
            activity = 1.465
        elif activity == 'active':
            activity = 1.55

        url = f'https://www.calculator.net/calorie-calculator.html?cage={age}&csex={gender[0]}&cheightfeet={height_feet}&cheightinch={height_inch}&cpound={weight}&cheightmeter=180&ckg=65&cactivity={activity}&cmop=0&coutunit=c&cformula=m&cfatpct=20&printit=0&ctype=standard&x=Calculate'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        tables = soup.find_all('table')
        if not tables or len(tables) < 2:
            raise ValueError("Calorie calculator data tables are missing or incomplete.")

        first_table = tables[0]
        second_table = tables[1]

        if desired_weight < weight:
            rows = first_table.find_all('tr')

            data = []
            for row in rows:
                try:
                    type_of_loss = row.find('div', class_='bigtext').text.strip()
                    calories = row.find('div', class_='verybigtext').find('b').text.strip().replace(',', '')
                    weekly_loss = row.find('div', style='color:#888;').text.strip() if row.find('div',
                                                                                                style='color:#888;') else "N/A"
                    data.append({
                        'Type': type_of_loss,
                        'Weekly Change': weekly_loss,
                        'Calories/Day': int(calories)
                    })
                except AttributeError:
                    continue  # Skip rows with missing data

            weightloss_df = pd.DataFrame(data)

            total_weight_to_lose = weight - desired_weight
            lbs_per_week = total_weight_to_lose / time_frame

            if 2.5 <= lbs_per_week:
                return None  # Not Suggested
            elif 1.8 < lbs_per_week <= 2.5:
                return int(weightloss_df['Calories/Day'].iloc[3]) if len(weightloss_df) > 3 else None
            elif 0.8 < lbs_per_week <= 1.8:
                return int(weightloss_df['Calories/Day'].iloc[2]) if len(weightloss_df) > 2 else None
            elif 0.2 < lbs_per_week <= 0.8:
                return int(weightloss_df['Calories/Day'].iloc[1]) if len(weightloss_df) > 1 else None
            else:
                return None

        elif desired_weight > weight:
            rows = second_table.find_all('tr')

            data = []
            for row in rows:
                try:
                    type_of_gain = row.find('div', class_='bigtext').text.strip()
                    calories = row.find('div', class_='verybigtext').find('b').text.strip().replace(',', '')
                    weekly_gain = row.find('div', style='color:#888;').text.strip()
                    data.append({
                        'Type': type_of_gain,
                        'Weekly Change': weekly_gain,
                        'Calories/Day': int(calories)
                    })
                except AttributeError:
                    continue  # Skip rows with missing data

            weightgain_df = pd.DataFrame(data)

            total_weight_to_gain = desired_weight - weight
            lbs_per_week = total_weight_to_gain / time_frame

            if 2.5 <= lbs_per_week:
                return None  # Not Suggested
            elif 1.8 < lbs_per_week <= 2.5:
                return int(weightgain_df['Calories/Day'].iloc[2]) if len(weightgain_df) > 2 else None
            elif 0.8 < lbs_per_week <= 1.8:
                return int(weightgain_df['Calories/Day'].iloc[1]) if len(weightgain_df) > 1 else None
            elif 0.2 < lbs_per_week <= 0.8:
                return int(weightgain_df['Calories/Day'].iloc[0]) if len(weightgain_df) > 0 else None
            else:
                return None

    def generate_protein_requirements(goal, weight):

        if goal == "Gain":
            protein = weight * 1
            return protein
        if goal == "Maintain":
            protein = weight * .8
            return protein
        if goal == "Lose":
            protein = weight * .5
            return protein

    def generate_shopping_list(weekly_diet_plan_df):
       pass