import os
import json
import requests
from datetime import datetime

# Fetching API Key from GitHub Secrets
API_KEY = os.environ.get('CMC_API_KEY')

# Premium Shariah Dictionaries for Classification
HARAM_TAGS = [
    'lending', 'borrowing', 'yield-farming', 'derivatives', 'options', 
    'casino', 'gambling', 'betting', 'adult', 'insurance', 'interest', 
    'prediction-markets', 'margin-trading'
]

DOUBTFUL_TAGS = [
    'centralized-exchange', 'synthetics', 'stablecoin-algorithm', 
    'memes', 'joke', 'doge', 'inu', 'pepe', 'animal', 'algorithmic-stablecoin'
]

HALAL_TAGS = [
    'layer-1', 'layer-2', 'smart-contracts', 'payments', 'web3', 
    'infrastructure', 'storage', 'pos', 'pow', 'ai', 'data', 'oracle',
    'enterprise', 'iot', 'logistics'
]

def analyze_shariah_compliance(name, tags_list, max_supply, circulating_supply):
    """
    Generates a deep, premium Shariah report based on Islamic Finance principles.
    """
    tags = [str(tag).lower() for tag in tags_list] if tags_list else []
    
    is_haram = False
    is_doubtful = False
    is_halal = False
    
    matched_haram_tags = []
    matched_doubtful_tags = []
    matched_halal_tags = []
    
    # 1. Categorize Tags
    for tag in tags:
        if any(word in tag for word in HARAM_TAGS):
            is_haram = True
            matched_haram_tags.append(tag)
        elif any(word in tag for word in DOUBTFUL_TAGS):
            is_doubtful = True
            matched_doubtful_tags.append(tag)
        elif any(word in tag for word in HALAL_TAGS):
            is_halal = True
            matched_halal_tags.append(tag)

    # 2. Risk & Tokenomics (Gharar) Check
    supply_warning = False
    gharar_report = "Tokenomics appear structurally transparent. "
    if max_supply is None:
        supply_warning = True
        gharar_report = "The project lacks a hard cap (maximum supply is unconstrained). From a Shariah perspective, this introduces a degree of 'Gharar' (uncertainty) regarding potential arbitrary inflation, asset devaluation, and supply manipulation. "
    else:
        gharar_report = f"A hard cap exists (Max Supply: {max_supply:,.0f}). This minimizes 'Gharar' (uncertainty) regarding arbitrary token printing and inflation. "

    # 3. Generating Deep Shariah Report Sections
    utility_report = ""
    riba_maysir_report = ""
    final_verdict = ""
    status = ""

    if is_haram:
        status = "HARAM"
        utility_report = "The core utility or primary ecosystem features conflict with Islamic financial principles."
        riba_maysir_report = f"Our algorithmic screening detected involvement in prohibited mechanisms: {', '.join(matched_haram_tags)}. In Islamic jurisprudence, these activities involve 'Riba' (usury/interest) or 'Maysir' (gambling/speculation), strictly rendering the asset non-compliant."
        final_verdict = "Non-Compliant (Haram). The project is fundamentally engaged in debt-based yield, excessive speculation, or prohibited industries."
        
    elif is_doubtful:
        status = "DOUBTFUL (Mashbooh)"
        if any(word in t for t in matched_doubtful_tags for word in ['memes', 'joke', 'doge']):
            utility_report = "This asset exhibits traits of a highly speculative nature (Meme coin) lacking intrinsic foundational utility or 'Mal' (recognized wealth)."
            riba_maysir_report = "While direct Riba may not be present, the asset heavily relies on hype and speculation, bordering on 'Maysir' (gambling)."
            final_verdict = "Doubtful/Highly Risky. Operates largely on speculative value without robust intrinsic utility, presenting excessive Gharar."
        else:
            utility_report = f"The project operates within gray areas of Islamic finance (e.g., {', '.join(matched_doubtful_tags)})."
            riba_maysir_report = "Potential indirect exposure to prohibited financial instruments. Centralized exchanges or synthetic assets often mix halal utility with haram trading pairs (margin/futures)."
            final_verdict = "Doubtful (Mashbooh). Mixed utility detected. Further independent scholarly auditing is highly recommended."

    elif is_halal:
        status = "HALAL"
        utility_report = f"The project demonstrates foundational blockchain utility (e.g., {', '.join(matched_halal_tags)}), operating within acceptable parameters of 'Mal' (valuable property)."
        riba_maysir_report = "No explicitly prohibited financial mechanisms (Riba) or speculative gambling protocols (Maysir) were detected in its core tag infrastructure."
        final_verdict = "Permissible (Halal). The asset demonstrates legitimate utility without direct contradiction to primary Shariah financial principles."
        
    else:
        # Fallback for projects with no tags or unknown tags
        status = "DOUBTFUL (Insufficient Data)"
        utility_report = "Lacks sufficient verifiable tag data to determine core blockchain utility."
        riba_maysir_report = "Unable to definitively clear the asset from Riba or Maysir due to lack of transparent infrastructure classification."
        final_verdict = "Doubtful. Inadequate data available to issue a clear compliance status. Avoidance is recommended until transparency improves."

    # Return the structured JSON object
    return {
        "Status": status,
        "Shariah_Report": {
            "Utility_and_Core_Concept": utility_report,
            "Financial_Screening_Riba_Maysir": riba_maysir_report,
            "Risk_and_Tokenomics_Gharar": gharar_report,
            "Final_Verdict": final_verdict
        }
    }

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
    
    # Fetching 10,000 coins (1 to 5000, 5001 to 10000)
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
            
            for coin in coins:
                coin_id = str(coin['id'])
                name = coin['name']
                symbol = coin['symbol']
                tags_list = coin.get('tags', [])
                
                # Fetching Tokenomics for Gharar Check
                max_supply = coin.get('max_supply')
                circulating_supply = coin.get('circulating_supply')
                
                # Run the premium logic
                analysis_result = analyze_shariah_compliance(name, tags_list, max_supply, circulating_supply)
                
                # Construct the final deeply structured object for the website
                all_crypto_data.append({
                    "Project_Profile": {
                        "id": coin_id,
                        "name": name,
                        "symbol": symbol,
                        "categories": tags_list if tags_list else ["Uncategorized"]
                    },
                    "Compliance_Status": analysis_result["Status"],
                    "Shariah_Report": analysis_result["Shariah_Report"],
                    "Last_Updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                })
                
        except Exception as e:
            print(f"Error fetching data: {e}")
    
    # Save the final structured data into JSON
    with open('crypto_data.json', 'w') as f:
        json.dump(all_crypto_data, f, indent=4)
        
    print(f"\n--- SUCCESS ---")
    print(f"Successfully processed and saved {len(all_crypto_data)} coins to crypto_data.json with Premium Shariah Reports.")

if __name__ == "__main__":
    fetch_and_analyze_crypto()
