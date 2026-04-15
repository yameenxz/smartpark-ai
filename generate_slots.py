import pandas as pd

slots = []

floors = {
    'A': 40,
    'B': 35,
    'C': 25
}

# Size distribution counters
small_count = 30
medium_count = 40
large_count = 30

size_pool = (
        ['Small'] * small_count +
        ['Medium'] * medium_count +
        ['Large'] * large_count
)

size_index = 0

for floor, total_slots in floors.items():
    for i in range(1, total_slots + 1):
        slot_number = f"{floor}-{i:02d}"

        # Assign size from pool
        slot_size = size_pool[size_index]
        size_index += 1

        # Assign zone based on position
        if i <= int(total_slots * 0.3):
            zone = "Near"
        elif i <= int(total_slots * 0.7):
            zone = "Middle"
        else:
            zone = "Far"

        slots.append({
            "slot_id": slot_number,
            "floor": floor,
            "slot_size": slot_size,
            "zone": zone
        })

df = pd.DataFrame(slots)

df.to_csv("parking_slots_dataset.csv", index=False)

print("Parking slot dataset generated successfully!")