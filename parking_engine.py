import sqlite3
import pickle
import pandas as pd

# ===============================
# Load trained model + encoders
# ===============================

with open("parking_model.pkl", "rb") as f:
    model, le_vehicle, le_day, le_purpose = pickle.load(f)

# ===============================
# Take User Input
# ===============================

vehicle_type = input("Enter vehicle type (SUV / Sedan / Hatchback): ").strip()
entry_hour = int(input("Enter entry hour (0-23): "))
day_type = input("Enter day type (Weekday / Weekend): ").strip()
visit_purpose = input("Enter visit purpose (Grocery / Shopping / Dining / Movies / Quick_Pickup / Office_Work): ").strip()

# ===============================
# Encode Inputs
# ===============================

vehicle_encoded = le_vehicle.transform([vehicle_type])[0]
day_encoded = le_day.transform([day_type])[0]
purpose_encoded = le_purpose.transform([visit_purpose])[0]

input_data = pd.DataFrame([{
    "vehicle_type": vehicle_encoded,
    "entry_hour": entry_hour,
    "day_type": day_encoded,
    "visit_purpose": purpose_encoded
}])

# ===============================
# Predict Duration
# ===============================

predicted_duration = model.predict(input_data)[0]

print("\nPredicted Duration:", round(predicted_duration, 2), "hours")

# ===============================
# Determine Zone
# ===============================

if predicted_duration < 2:
    required_zone = "Near"
elif predicted_duration <= 4:
    required_zone = "Middle"
else:
    required_zone = "Far"

# ===============================
# Determine Slot Size
# ===============================

if vehicle_type == "SUV":
    required_size = "Large"
elif vehicle_type == "Sedan":
    required_size = "Medium"
else:
    required_size = "Small"

# ===============================
# Connect to Database
# ===============================

conn = sqlite3.connect("parking_system.db")
cursor = conn.cursor()

cursor.execute("""
               SELECT slot_id FROM parking_slots
               WHERE slot_size = ?
                 AND zone = ?
                 AND is_available = 1
                   LIMIT 1
               """, (required_size, required_zone))

result = cursor.fetchone()

if result:
    assigned_slot = result[0]

    cursor.execute("""
                   UPDATE parking_slots
                   SET is_available = 0
                   WHERE slot_id = ?
                   """, (assigned_slot,))

    conn.commit()

    print("Assigned Slot:", assigned_slot)
else:
    print("No suitable slot available.")

conn.close()