import json
import time
import requests

def get_top_crypto_ids():
    print("Fetching crypto page 33 to 40 (Coins 8001 to 10000) from CoinGecko...")
    coin_ids = []
    headers = {'User-Agent': 'HalalScreenerApp (contact@example.com)'}
    
    for page in range(33, 41): # Page 33 to 40
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page={page}&sparkline=false"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if not data: 
                    break
                for coin in data:
                    coin_ids.append({"id": coin['id'], "symbol": coin['symbol'].upper(), "name": coin['name']})
            elif response.status_code == 429:
                time.sleep(60)
                continue
            time.sleep(10) 
        except Exception as e:
            pass
    return coin_ids

def analyze_crypto_compliance(coin_id, name, symbol):
    headers = {'User-Agent': 'HalalScreenerApp (contact@example.com)'}
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                time.sleep(60)
                continue
            if response.status_code != 200:
                return None
                
            data = response.json()
            categories = [cat.lower() for cat in data.get('categories', []) if cat]
            
            haram_keywords = ['lending', 'borrowing', 'yield', 'derivative', 'option', 'casino', 'gambling', 'betting', 'adult', 'insurance', 'interest']
            meme_keywords = ['meme', 'joke', 'doge', 'inu', 'pepe', 'animal']
            
            is_haram = False
            is_meme = False
            haram_reason = ""
            
            for cat in categories:
                if any(word in cat for word in haram_keywords):
                    is_haram = True
                    haram_reason = cat
                    break
            if not is_haram:
                for cat in categories:
                    if any(word in cat for word in meme_keywords):
                        is_meme = True
                        haram_reason = cat
                        break

            report = {
                "categories_found": data.get('categories', []),
                "riba_and_gambling_status": {"pass": not is_haram, "details": "Failed due to Riba/Gambling" if is_haram else "No interest/gambling detected."},
                "utility_and_gharar_status": {"pass": not is_meme, "details": "Failed due to Gharar/Meme" if is_meme else "Legitimate utility found."}
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
            return {"id": coin_id, "name": name, "symbol": symbol, "status": status, "report": report}
        except Exception:
            pass
    return None

def update_crypto_data():
    coins = get_top_crypto_ids()
    crypto_data = []
    
    for idx, coin in enumerate(coins):
        result = analyze_crypto_compliance(coin['id'], coin['name'], coin['symbol'])
        if result:
            crypto_data.append(result)
        time.sleep(6)

    with open('crypto_data_5.json', 'w') as f:
        json.dump(crypto_data, f, indent=4)

if __name__ == "__main__":
    update_crypto_data()
