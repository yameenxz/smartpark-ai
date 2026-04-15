import pandas as pd

# Load parking slots
slots_df = pd.read_csv("parking_slots_dataset.csv")

# Simulated car input (later this will come from ML model)
vehicle_type = "SUV"
predicted_duration = 4.5  # Example ML output

# Convert duration to category
if predicted_duration < 2:
    stay_category = "Near"
elif predicted_duration <= 4:
    stay_category = "Middle"
else:
    stay_category = "Far"

# Determine required slot size
if vehicle_type == "SUV":
    required_size = "Large"
elif vehicle_type == "Sedan":
    required_size = "Medium"
else:
    required_size = "Small"

# Filter matching slots
matching_slots = slots_df[
    (slots_df["slot_size"] == required_size) &
    (slots_df["zone"] == stay_category)
    ]

# Pick first matching slot
if not matching_slots.empty:
    assigned_slot = matching_slots.iloc[0]["slot_id"]
    print("Assigned Slot:", assigned_slot)
else:
    print("No suitable slot available.")