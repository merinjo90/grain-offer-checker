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

# --- Planted problems for testing the checker (documented in README) ---
records[4]["supplier"] = ""                              # OFF-005: missing supplier
records[7]["offer_id"] = "OFF-007"                       # OFF-008: duplicate ID
records[10]["quantity"] = -2                             # OFF-011: negative quantity
records[13]["unit_price_eur"] = "abc"                    # OFF-014: invalid number
records[16]["total_price_eur"] += 5000                   # OFF-017: total mismatch
records[19]["offer_date"] = "2026-02-30"                 # OFF-020: invalid date
records[22]["valid_until"] = "2025-12-01"                # OFF-023: valid_until before offer_date
records[25]["capacity_t"] = 50000                        # OFF-026: capacity out of range
records[28]["delivery_weeks"] = 80                       # OFF-029: delivery weeks out of range
records[31]["equipment_type"] = "elevator"               # OFF-032: equipment type not allowed
records[34]["equipment_type"] = " Silo "                 # OFF-035: formatting only (safe fix)
records[37]["supplier"] = "  Synthetic Supplier C"       # OFF-038: formatting only (safe fix)

df = pd.DataFrame(records)
df.to_csv(OUTPUT_PATH, index=False)

print(df.head())
print("Rows:", len(df))
