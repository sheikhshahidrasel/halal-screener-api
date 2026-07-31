import json
import os

all_data = []

if os.path.exists('crypto_data_1.json'):
    with open('crypto_data_1.json', 'r') as f:
        all_data.extend(json.load(f))

if os.path.exists('crypto_data_2.json'):
    with open('crypto_data_2.json', 'r') as f:
        all_data.extend(json.load(f))

# Save the final merged data
with open('crypto_data.json', 'w') as f:
    json.dump(all_data, f, indent=4)
    
print(f"Successfully merged {len(all_data)} coins into crypto_data.json")
