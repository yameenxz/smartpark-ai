import sqlite3

conn = sqlite3.connect("parking_system.db")
cursor = conn.cursor()

cursor.execute("UPDATE parking_slots SET is_available = 1")

conn.commit()
conn.close()

print("All slots have been reset to available.")