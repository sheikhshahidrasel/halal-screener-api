import os
import json
import requests

# Fetching API Key from GitHub Secrets
API_KEY = os.environ.get('CMC_API_KEY')

def fetch_and_analyze_crypto():
    if not API_KEY:
        print("Error: CMC_API_KEY not found in environment variables. Please check GitHub Secrets.")
        return

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }
    
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    all_crypto_data = []
    
    # We need 10,000 coins. CoinMarketCap allows a maximum of 5,000 per request.
    # So we make 2 requests: 1 to 5000, and 5001 to 10000.
    start_points = [1, 5001]
    
    for start in start_points:
        print(f"Fetching coins from rank {start} to {start + 4999}...")
        params = {
            'start': str(start),
            'limit': '5000',
            'convert': 'USD'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if response.status_code != 200:
                print(f"API Error: {data.get('status', {}).get('error_message', 'Unknown error')}")
                continue
                
            coins = data.get('data', [])
            
            # Shariah Screening Keywords
            haram_keywords = ['lending', 'borrowing', 'yield', 'derivative', 'option', 'casino', 'gambling', 'betting', 'adult', 'insurance', 'interest']
            meme_keywords = ['meme', 'joke', 'doge', 'inu', 'pepe', 'animal']
            
            for coin in coins:
                coin_id = str(coin['id'])
                name = coin['name']
                symbol = coin['symbol']
                
                # CoinMarketCap uses 'tags' instead of 'categories'
                tags_list = coin.get('tags', [])
                # Handle cases where tags might be None
                if not tags_list:
                    tags_list = []
                    
                tags = [str(tag).lower() for tag in tags_list]
                
                is_haram = False
                is_meme = False
                haram_reason = ""
                
                # Check for Riba / Gambling (Haram)
                for tag in tags:
                    if any(word in tag for word in haram_keywords):
                        is_haram = True
                        haram_reason = tag
                        break
                        
                # Check for Gharar / Meme
                if not is_haram:
                    for tag in tags:
                        if any(word in tag for word in meme_keywords):
                            is_meme = True
                            haram_reason = tag
                            break
                            
                # Generate Detailed Shariah Report (Matching your previous format perfectly)
                report = {
                    "categories_found": tags_list,
                    "riba_and_gambling_status": {
                        "pass": not is_haram, 
                        "details": "Failed due to Riba/Gambling" if is_haram else "No interest/gambling detected."
                    },
                    "utility_and_gharar_status": {
                        "pass": not is_meme, 
                        "details": "Failed due to Gharar/Meme" if is_meme else "Legitimate utility found."
                    }
                }
                
                if is_haram:
                    status = "HARAM"
                    final_verdict = f"Prohibited. Operates in '{haram_reason.title()}'. Involves Riba or Maysir."
                elif is_meme:
                    status = "HARAM"
                    final_verdict = f"Prohibited. Speculative asset class: '{haram_reason.title()}'. Involves Gharar."
                else:
                    status = "HALAL"
                    final_verdict = "Permissible. Foundational blockchain utility detected without Riba/Maysir."
                    
                report["final_verdict"] = final_verdict
                
                all_crypto_data.append({
                    "id": coin_id,
                    "name": name,
                    "symbol": symbol,
                    "status": status,
                    "report": report
                })
                
        except Exception as e:
            print(f"Error fetching data: {e}")
    
    # Save the final data into JSON
    with open('crypto_data.json', 'w') as f:
        json.dump(all_crypto_data, f, indent=4)
        
    print(f"\n--- SUCCESS ---")
    print(f"Successfully processed and saved {len(all_crypto_data)} coins to crypto_data.json")

if __name__ == "__main__":
    fetch_and_analyze_crypto()
