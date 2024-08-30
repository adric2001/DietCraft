import openai
import os
import pandas as pd
from io import StringIO
import csv

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


def main():
    print("Welcome to DietCraft!")

    calories = int(input("Enter daily calorie goal (e.g., 1900): "))
    protein = int(input("Enter daily protein goal in grams (e.g., 125): "))

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
