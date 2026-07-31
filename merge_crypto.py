import json
import os

all_data = []

# Loop through all 5 generated JSON files (crypto_data_1.json to crypto_data_5.json)
for i in range(1, 6):
    file_name = f'crypto_data_{i}.json'
    
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
                print(f"Successfully loaded {len(data)} coins from {file_name}")
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
    else:
        print(f"Warning: {file_name} was not found.")

# Save the final merged data into crypto_data.json
with open('crypto_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print(f"\n--- SUCCESS ---")
print(f"Successfully merged a total of {len(all_data)} coins into crypto_data.json")
