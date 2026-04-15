import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle

df = pd.read_csv("synthetic_parking_dataset.csv")

# Encoders
le_vehicle = LabelEncoder()
le_day = LabelEncoder()
le_purpose = LabelEncoder()

df["vehicle_type"] = le_vehicle.fit_transform(df["vehicle_type"])
df["day_type"] = le_day.fit_transform(df["day_type"])
df["visit_purpose"] = le_purpose.fit_transform(df["visit_purpose"])

X = df[["vehicle_type", "entry_hour", "day_type", "visit_purpose"]]
y = df["stay_duration"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor()
model.fit(X_train, y_train)

mae = abs(model.predict(X_test) - y_test).mean()
print("Model trained successfully.")
print("Mean Absolute Error:", round(mae, 2), "hours")

# IMPORTANT: Save ALL 4 objects
with open("parking_model.pkl", "wb") as f:
    pickle.dump((model, le_vehicle, le_day, le_purpose), f)

print("Model saved correctly.")