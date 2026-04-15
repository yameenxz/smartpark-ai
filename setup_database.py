import sqlite3
import pandas as pd

# Connect to SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect("parking_system.db")
cursor = conn.cursor()

# Create parking_slots table
cursor.execute("""
               CREATE TABLE IF NOT EXISTS parking_slots (
                                                            slot_id TEXT PRIMARY KEY,
                                                            floor TEXT,
                                                            slot_size TEXT,
                                                            zone TEXT,
                                                            is_available INTEGER
               )
               """)

# Load parking slot dataset
slots_df = pd.read_csv("parking_slots_dataset.csv")

# Insert slots into database
for _, row in slots_df.iterrows():
    cursor.execute("""
                   INSERT INTO parking_slots (slot_id, floor, slot_size, zone, is_available)
                   VALUES (?, ?, ?, ?, ?)
                   """, (
                       row["slot_id"],
                       row["floor"],
                       row["slot_size"],
                       row["zone"],
                       1  # Initially all slots available
                   ))

conn.commit()
conn.close()

print("Database setup complete. Slots loaded successfully.")