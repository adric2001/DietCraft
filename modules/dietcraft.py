# modules/dietcraft.py
import pandas as pd
from io import StringIO
import csv
import requests
from bs4 import BeautifulSoup

class DietCraft:
    def __init__(self):
        pass

    def generate_weekly_diet_plan(calories, protien):
        pass

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
        first_table = tables[0]
        second_table = tables[1]


        if desired_weight < weight:

            # Find the table rows
            rows = first_table.find_all('tr')

            # Extract data into a list of dictionaries
            data = []
            for row in rows:
                type_of_loss = row.find('div', class_='bigtext').text.strip()
                calories = row.find('div', class_='verybigtext').find('b').text.strip()
                weekly_loss = row.find('div', style='color:#888;').text.strip() if row.find('div',
                                                                                            style='color:#888;') else "N/A"
                data.append({
                    'Type': type_of_loss,
                    'Weekly Change': weekly_loss,
                    'Calories/Day': calories
                })

            # Convert the list of dictionaries into a DataFrame
            weightloss_df = pd.DataFrame(data)


            total_weight_to_lose = weight - desired_weight
            lbs_per_week = total_weight_to_lose / time_frame

            print(lbs_per_week)

            if 2.5 <= lbs_per_week:
                return "Not Suggested"
            elif 1.8 < lbs_per_week < 2.5 :
                return f"Based on your current settings your calorie requirement is {weightloss_df['Calories/Day'][3]} a day"
            elif 0.8 < lbs_per_week < 1.8:
                return f"Based on your current settings your calorie requirement is {weightloss_df['Calories/Day'][2]} a day"
            elif .2 < lbs_per_week < 0.8:
                return f"Based on your current settings your calorie requirement is {weightloss_df['Calories/Day'][1]} a day"
            else:
                return "Not a significant enough change, decrease your time frame or decrease your weight."

        elif desired_weight > weight:

            # Extract data into a list of dictionaries for DataFrame
            data = []
            rows = second_table.find_all('tr')
            for row in rows:
                type_of_gain = row.find('div', class_='bigtext').text.strip()
                calories = row.find('div', class_='verybigtext').find('b').text.strip()
                weekly_gain = row.find('div', style='color:#888;').text.strip()
                data.append({
                    'Type': type_of_gain,
                    'Weekly Change': weekly_gain,
                    'Calories/Day': calories
                })

            # Convert the list of dictionaries into a DataFrame
            weightgain_df = pd.DataFrame(data)

            total_weight_to_gain = desired_weight - weight
            lbs_per_week = total_weight_to_gain / time_frame

            if 2.5 <= lbs_per_week:
                return "Not Suggested"
            elif 1.8 < lbs_per_week < 2.5:
                return f"Based on your current settings your calorie requirement is {weightgain_df['Calories/Day'][2]} a day"
            elif .8 < lbs_per_week < 1.8:
                return f"Based on your current settings your calorie requirement is {weightgain_df['Calories/Day'][1]} a day"
            elif .2 < lbs_per_week < .8:
                return f"Based on your current settings your calorie requirement is {weightgain_df['Calories/Day'][0]} a day"
            else:
                return "Not a significant enough change, decrease your time frame or increase your weight."

    def generate_protein_requirements(goal, weight):

        if goal == "Gain Muscle":
            protein = weight * .9
            return protein
        if goal == "Maintain Muscle":
            protein = weight * .5
            return protein

    def generate_shopping_list(weekly_diet_plan_df):
       pass