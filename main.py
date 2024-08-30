import openai
import os
import pandas as pd
from io import StringIO
import csv
import requests
from bs4 import BeautifulSoup

openai.api_key = os.getenv('api-key')

def generate_weekly_diet_plan(calories, protein):
    # Your prompt and API call
    prompt = (
        f"Create a weekly diet plan (from Monday to Sunday) with no more than {calories} calories per day "
        f"and at least {protein} grams of protein per day. "
        f"Format the response as a csv with the following columns: 'Day', 'Type (Breakfast, Lunch, Dinner, Snack)', 'Details', 'Calories', 'Carbs', 'Protein', 'Fat'. "
        f"Ensure that each field is properly quoted if it contains commas and only contains the csv without '''csv."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )

    # Extract the CSV data
    csv_data = response.choices[0]['message']['content'].strip()

    # Create a StringIO object
    csv_buffer = StringIO(csv_data)

    # Read the CSV data into a DataFrame with error handling for inconsistent rows
    try:
        df = pd.read_csv(csv_buffer, quoting=csv.QUOTE_MINIMAL)
        return df
    except pd.errors.ParserError as e:
        print("Error parsing CSV data:", e)

def generate_shopping_list(weekly_diet_plan_df):
    # Convert the DataFrame back to a CSV string for the prompt
    plan_summary = weekly_diet_plan_df.to_csv(index=False, header=True)

    prompt = (
        f"Based on the following weekly diet plan, generate a shopping list. "
        f"Format the shopping list as 'Item, Quantity' in CSV format. Only include the csv without '''csv."
        f"Here is the plan:\n{plan_summary}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )

    shopping_list_csv = response.choices[0]['message']['content'].strip()

    # Create a StringIO object
    csv_buffer = StringIO(shopping_list_csv)

    # Read the CSV data into a DataFrame with error handling for inconsistent rows
    try:
        df = pd.read_csv(csv_buffer, quoting=csv.QUOTE_MINIMAL)
        return df
    except pd.errors.ParserError as e:
        print("Error parsing CSV data:", e)

def generate_calorie_requirements(age, gender, height_feet, height_inch, weight, desired_weight, time_frame, activity):

    if activity == 'Light':
        activity = 1.375
    elif activity == 'Moderate':
        activity = 1.465
    elif activity == 'Active':
        activity = 1.55

    url = f'https://www.calculator.net/calorie-calculator.html?cage={age}&csex={gender}&cheightfeet={height_feet}&cheightinch={height_inch}&cpound={weight}&cheightmeter=180&ckg=65&cactivity={activity}&cmop=0&coutunit=c&cformula=m&cfatpct=20&printit=0&ctype=standard&x=Calculate'
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

        if 2.5 < lbs_per_week:
            return "Not Suggested"
        elif 1.8 < lbs_per_week < 2.5 :
            return weightloss_df['Calories/Day'][3]
        elif 0.8 < lbs_per_week < 1.8:
            return weightloss_df['Calories/Day'][2]
        elif .2 < lbs_per_week < 0.8:
            return weightloss_df['Calories/Day'][1]
        else:
            return "Maintaining"

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

        if 2.5 < lbs_per_week:
            return "Not Suggested"
        elif 1.8 < lbs_per_week < 2.5:
            return weightgain_df['Calories/Day'][2]
        elif .8 < lbs_per_week < 1.8:
            return weightgain_df['Calories/Day'][1]
        elif .2 < lbs_per_week < .8:
            return weightgain_df['Calories/Day'][0]
        else:
            return "Maintaining"

def generate_protein_requirements(goal, weight):

    if goal == "gain":
        protein = weight * .9
        return protein
    if goal == "maintain":
        protein = weight * .5
        return protein



def main():
    print("Welcome to DietCraft!")

    age = int(input("What is your age?"))
    gender = input("What is your gender [m/f]?")
    height_feet = int(input("What is your height in feet?"))
    height_inches = int(input("What is your height in inches?"))
    desired_weight = int(input("What is your desired_weight in lbs?"))
    current_weight = int(input("What is your current weight in lbs?"))
    activity_level = input("What is your activity level [Light, Moderate, Active]")
    time_frame = int(input("What is your timeframe in weeks?"))
    goal = input("Are you wanting to gain or maintain muscle [gain/maintain]?")

    calories = generate_calorie_requirements(age, gender, height_feet, height_inches, current_weight, desired_weight, time_frame, activity_level)
    protein = generate_protein_requirements(goal, current_weight)
    print(f"You require {calories} calories and {protein} grams of protein for your plan.")

    print("\nGenerating your weekly diet plan...")
    weekly_diet_plan_df = generate_weekly_diet_plan(calories, protein)

    print("\nWeekly Diet Plan:")
    print(weekly_diet_plan_df)

    print("\nGenerating your shopping list...")
    shopping_list_df = generate_shopping_list(weekly_diet_plan_df)

    print("\nWeekly Shopping List:")
    print(shopping_list_df)


if __name__ == "__main__":
    main()
