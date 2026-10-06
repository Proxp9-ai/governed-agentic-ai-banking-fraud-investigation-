
from pathlib import Path

import pandas as pd

# Reproducible synthetic demonstration data.
records = [
    {
        "transaction_id": "TXN-1001",
        "amount": 5000,
        "channel": "UPI",
        "location": "Usual Location",
        "device": "Recognised Device",
        "failed_logins": 0,
        "label": 0,
    },
    {
        "transaction_id": "TXN-1002",
        "amount": 75000,
        "channel": "Internet Banking",
        "location": "New Location",
        "device": "New Device",
        "failed_logins": 4,
        "label": 1,
    },
    {
        "transaction_id": "TXN-1003",
        "amount": 1200,
        "channel": "Card",
        "location": "Usual Location",
        "device": "Recognised Device",
        "failed_logins": 0,
        "label": 0,
    },
    {
        "transaction_id": "TXN-1004",
        "amount": 32000,
        "channel": "UPI",
        "location": "New Location",
        "device": "Recognised Device",
        "failed_logins": 1,
        "label": 0,
    },
    {
        "transaction_id": "TXN-1005",
        "amount": 95000,
        "channel": "Mobile Banking",
        "location": "New Location",
        "device": "New Device",
        "failed_logins": 5,
        "label": 1,
    },
    {
        "transaction_id": "TXN-1006",
        "amount": 8500,
        "channel": "ATM",
        "location": "Usual Location",
        "device": "New Device",
        "failed_logins": 2,
        "label": 0,
    },
]

output_path = (
    Path(__file__).parent
    / "data"
    / "synthetic"
    / "transactions.csv"
)

output_path.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(records)
df.to_csv(output_path, index=False)

print(f"Created {len(df)} synthetic transactions.")
print(f"Saved dataset to: {output_path}")
print()
print(df.to_string(index=False))
