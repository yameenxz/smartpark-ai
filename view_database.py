import sqlite3

conn = sqlite3.connect("parking_system.db")
cursor = conn.cursor()

cursor.execute("SELECT slot_id, is_available FROM parking_slots")
rows = cursor.fetchall()

print("Total rows:", len(rows))
print("\nOccupied Slots:\n")

for row in rows:
    if row[1] == 0:
        print(row)

conn.close()