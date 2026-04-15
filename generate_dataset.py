import pandas as pd
import random

vehicle_types = ["SUV", "Sedan", "Hatchback"]
day_types = ["Weekday", "Weekend"]
visit_purposes = [
    "Grocery",
    "Shopping",
    "Dining",
    "Movies",
    "Quick_Pickup",
    "Office_Work"
]

data = []

for _ in range(800):  # Increase rows for better training
    vehicle = random.choice(vehicle_types)
    entry_hour = random.randint(8, 22)
    day = random.choice(day_types)
    purpose = random.choice(visit_purposes)

    # Duration logic based on purpose
    if purpose == "Quick_Pickup":
        duration = round(random.uniform(0.1, 0.5), 2)
    elif purpose == "Grocery":
        duration = round(random.uniform(0.5, 1.5), 2)
    elif purpose == "Dining":
        duration = round(random.uniform(1, 2), 2)
    elif purpose == "Shopping":
        duration = round(random.uniform(1, 3), 2)
    elif purpose == "Movies":
        duration = round(random.uniform(2.5, 4), 2)
    else:  # Office_Work
        duration = round(random.uniform(3, 6), 2)

    data.append([vehicle, entry_hour, day, purpose, duration])

df = pd.DataFrame(data, columns=[
    "vehicle_type",
    "entry_hour",
    "day_type",
    "visit_purpose",
    "stay_duration"
])

df.to_csv("synthetic_parking_dataset.csv", index=False)

print("Dataset generated successfully.")