"""Generate SYNTHETIC grain-storage equipment offers for demonstration.

All data is fictional and does not represent any real company or supplier.
"""
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

EQUIPMENT_TYPES = ["silo", "conveyor", "dryer", "cleaner"]
OUTPUT_PATH = "data/raw/synthetic_offers.csv"


def make_clean_offer(number):
    equipment = random.choice(EQUIPMENT_TYPES)
    quantity = random.randint(1, 4)
    unit_price = random.randint(10, 200) * 1000
    offer_date = date(2026, 1, 1) + timedelta(days=random.randint(0, 180))

    # EXERCISE: set capacity based on the equipment type

    if equipment == "silo":
        capacity = random.randint(500, 15000)
    else:
        capacity = random.randint(20, 300)

    return {
        "offer_id": f"OFF-{number:03d}",
        "supplier": f"Synthetic Supplier {random.choice('ABCDE')}",
        "equipment_type": equipment,
        "capacity_t": capacity,
        "quantity": quantity,
        "unit_price_eur": unit_price,
        "total_price_eur": quantity * unit_price,
        "offer_date": offer_date.isoformat(),
        "valid_until": (offer_date + timedelta(days=90)).isoformat(),
        "delivery_weeks": random.randint(4, 30),
        "data_source": "ai_extracted" if random.random() < 0.2 else "manual_entry",
    }


records = [make_clean_offer(n) for n in range(1, 46)]
df = pd.DataFrame(records)
df.to_csv(OUTPUT_PATH, index=False)

print(df.head())
print("Rows:", len(df))
