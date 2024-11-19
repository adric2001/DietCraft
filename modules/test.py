import requests
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()


print(generate_calorie_requirements(25, 'male', 5, 10, 180, 160, 12, 'moderate'))
print(generate_calorie_requirements(25, 'female', 5, 4, 150, 170, 12, 'active'))

