import os
import json
import time
import random
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if type(obj) == type:
            return str(obj)
        return super(NumpyEncoder, self).default(obj)

# Robust Session with Retry Mechanism to prevent connection drops
def get_robust_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Premium Shariah Dictionaries for Business Sector Screening
HARAM_INDUSTRIES = [
    'tobacco', 'casinos & gaming', 'aerospace & defense', 'banks - regional', 
    'banks - diversified', 'insurance - life', 'insurance - property & casualty', 
    'insurance - diversified', 'insurance - reinsurance', 'insurance - specialty',
    'confectioners', 'liquor', 'brewers', 'wines & spirits', 'entertainment',
    'gambling', 'pork', 'adult'
]

DOUBTFUL_INDUSTRIES = [
    'broadcasting', 'media', 'movies & entertainment', 'asset management', 
    'capital markets', 'financial data & stock exchanges', 'credit services'
]

def fetch_wiki_tickers(session, url, suffix):
    tickers = []
    try:
        headers = {'User-Agent': 'PremiumShariahScreener (contact@example.com)'}
        response = session.get(url, headers=headers, timeout=15)
        tables = pd.read_html(response.text)
        
        for df in tables:
            target_col = None
            for col in df.columns:
                if any(keyword in str(col).upper() for keyword in ['TICKER', 'SYMBOL', 'CODE']):
                    target_col = col
                    break
            
            if target_col:
                for val in df[target_col].dropna().astype(str):
                    clean_val = str(val).split()[0].replace('.', '')
                    if 1 <= len(clean_val) <= 6 and clean_val.upper() != 'SYMBOL':
                        tickers.append(f"{clean_val}.{suffix}")
                break
    except Exception as e:
        print(f"Skipping Wiki fetch for {suffix}: {e}")
    return tickers

def get_netherlands_tickers():
    netherlands_tickers = set()
    session = get_robust_session()

    # Fetch Major Netherlands Indices via Wikipedia Automatically (Euronext Amsterdam)
    # AEX (Top 25), AMX (Midcap), AScX (Smallcap) to cover the full market
    wiki_sources = [
        ("https://en.wikipedia.org/wiki/AEX_index", "AS"),
        ("https://en.wikipedia.org/wiki/AMX_index", "AS"),
        ("https://en.wikipedia.org/wiki/AScX_index", "AS")
    ]
    
    print("Fetching official Netherlands (Euronext Amsterdam) stock list automatically...")
    for url, suffix in wiki_sources:
        fetched = fetch_wiki_tickers(session, url, suffix)
        netherlands_tickers.update(fetched)
        print(f"Loaded {len(fetched)} tickers from index source.")
        time.sleep(2)

    final_tickers = list(netherlands_tickers)
    print(f"Successfully compiled a total of {len(final_tickers)} unique Netherlands tickers.")
    
    # Fallback in case Wikipedia structure changes or network fails
    if len(final_tickers) < 5:
         return ["ASML.AS", "HEIA.AS", "INGA.AS", "ADYEN.AS", "PHIA.AS"]
    
    return final_tickers

def extract_financial_value(dataframe, keys):
    """Helper function to safely extract values from yfinance dataframes"""
    for key in keys:
        if key in dataframe.index:
            val = dataframe.loc[key]
            if isinstance(val, pd.Series):
                return float(val.iloc[0]) if not pd.isna(val.iloc[0]) else 0.0
            return float(val) if not pd.isna(val) else 0.0
    return 0.0

def generate_scholarly_report(company_name, sector, industry, is_haram_business, missing_data, ratios, passes):
    """Generates the deeply structured premium narrative report"""
    
    business_report = ""
    financial_report = ""
    dividend_report = ""
    verdict = ""
    status = ""
    
    # 1. Business Screening Logic
    if is_haram_business:
        business_report = f"According to industry classification, {company_name} operates within the '{industry.title()}' sector. Core operations in this sector directly contradict Islamic principles, rendering the primary business activity Non-Permissible (Haram)."
        status = "HARAM"
        verdict = f"Non-Compliant. Investment in {company_name} is prohibited due to its core business operations violating Shariah guidelines."
    else:
        business_report = f"The primary business operations of {company_name} fall under '{industry.title()}' within the {sector.title()} sector, which is generally considered permissible (Halal) under Shariah guidelines."
        
    # 2. Handle Missing Data
    if missing_data and not is_haram_business:
        return {
            "Compliance_Status": "DOUBTFUL",
            "Business_Screening": {"status": "Passed", "report": business_report},
            "Financial_Screening": {"report": "Insufficient financial data available to perform a comprehensive AAOIFI mathematical screening. Avoidance is recommended until balance sheet transparency improves."},
            "Dividend_Purification": {"purification_rate": 0.0, "report": "N/A"},
            "Scholarly_Verdict": "Doubtful (Mashbooh) due to lack of verifiable financial metrics."
        }

    if is_haram_business:
        financial_report = "Financial screening is secondary as the core business is strictly prohibited."
        purification_report = "Not applicable for strictly prohibited equities."
    else:
        # 3. Financial Screening Logic (AAOIFI Standard)
        fin_details = []
        
        # Debt
        if passes['debt']:
            fin_details.append(f"Total Debt to Assets ratio is {ratios['debt']:.2f}%, comfortably below the globally recognized AAOIFI maximum threshold of 33.0%.")
        else:
            fin_details.append(f"Total Debt to Assets ratio is {ratios['debt']:.2f}%, strictly exceeding the Shariah-compliant threshold of 33.0%. This indicates excessive reliance on interest-bearing leverage (Riba).")
            
        # Cash
        if passes['cash']:
            fin_details.append(f"Liquid Assets (Cash & Equivalents) ratio stands at {ratios['cash']:.2f}%, within the permissible 33.0% limit.")
        else:
            fin_details.append(f"Liquid Assets ratio is {ratios['cash']:.2f}%, exceeding the 33.0% limit, violating the principle regarding the exchange of highly liquid assets.")
            
        # Receivables
        if passes['receivables']:
            fin_details.append(f"Accounts Receivable ratio is {ratios['receivables']:.2f}%, compliant with the 45.0% maximum threshold.")
        else:
            fin_details.append(f"Accounts Receivable ratio is {ratios['receivables']:.2f}%, exceeding the 45.0% threshold, indicating structural issues with debt-based sales.")

        financial_report = " ".join(fin_details)
        
        # 4. Dividend Purification Logic
        if ratios['npi'] > 0 and ratios['npi'] < 5.0:
            purification_report = f"A minor portion of revenue ({ratios['npi']:.2f}%) is derived from Non-Permissible Income (e.g., interest). Investors are advised to purify their dividends by donating {ratios['npi']:.2f}% to charity."
        elif ratios['npi'] >= 5.0:
            purification_report = f"Non-Permissible Income exceeds the 5% tolerance limit ({ratios['npi']:.2f}%). This renders the asset strictly Haram."
        else:
            purification_report = "No significant Non-Permissible Income (Interest) detected. Purification requirements are minimal."

        # 5. Final Status & Verdict
        if not passes['debt'] or not passes['cash'] or not passes['receivables'] or not passes['npi']:
            status = "HARAM"
            verdict = f"Non-Compliant. Although the core operations are permissible, {company_name}'s capital structure severely violates Shariah financial guidelines. Investment is prohibited until financial ratios are restructured."
        else:
            status = "HALAL"
            verdict = f"Permissible (Halal). {company_name} successfully passes both business activity and AAOIFI financial screening standards."

    return {
        "Compliance_Status": status,
        "Business_Screening": {
            "status": "Failed" if is_haram_business else "Passed",
            "report": business_report
        },
        "Financial_Screening": {
            "metrics": {
                "Debt_to_Assets": {"value": round(ratios['debt'], 2), "limit": "< 33.0%", "passed": passes['debt']},
                "Cash_to_Assets": {"value": round(ratios['cash'], 2), "limit": "< 33.0%", "passed": passes['cash']},
                "Receivables_to_Assets": {"value": round(ratios['receivables'], 2), "limit": "< 45.0%", "passed": passes['receivables']},
                "Non_Permissible_Income": {"value": round(ratios['npi'], 2), "limit": "< 5.0%", "passed": passes['npi']}
            },
            "report": financial_report
        },
        "Dividend_Purification": {
            "purification_rate_percentage": round(ratios['npi'], 2),
            "report": purification_report
        },
        "Scholarly_Verdict": verdict
    }

def check_shariah_compliance(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('shortName', info.get('longName', ticker))
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')

        # Business Sector Screening
        industry_lower = str(industry).lower()
        is_haram_business = any(haram_word in industry_lower for haram_word in HARAM_INDUSTRIES)

        bs = stock.balance_sheet
        fin = stock.financials

        total_assets = 0.0
        total_debt = 0.0
        cash_investments = 0.0
        accounts_receivable = 0.0
        total_revenue = 0.0
        interest_income = 0.0
        missing_data = False

        if bs.empty or fin.empty:
            missing_data = True
        else:
            total_assets = extract_financial_value(bs, ['Total Assets'])
            total_debt = extract_financial_value(bs, ['Total Debt', 'Long Term Debt', 'Current Debt'])
            cash = extract_financial_value(bs, ['Cash And Cash Equivalents', 'Cash', 'Operating Cash'])
            short_term = extract_financial_value(bs, ['Other Short Term Investments', 'Short Term Investments'])
            cash_investments = cash + short_term
            accounts_receivable = extract_financial_value(bs, ['Net Receivables', 'Accounts Receivable', 'Receivables'])
            
            total_revenue = extract_financial_value(fin, ['Total Revenue', 'Operating Revenue'])
            interest_income = extract_financial_value(fin, ['Interest Income', 'Non Operating Income/Expense'])

            if total_assets == 0 or total_revenue == 0:
                missing_data = True

        # Math Engine (AAOIFI Standard)
        ratios = {'debt': 0.0, 'cash': 0.0, 'receivables': 0.0, 'npi': 0.0}
        passes = {'debt': False, 'cash': False, 'receivables': False, 'npi': False}

        if not missing_data:
            ratios['debt'] = (total_debt / total_assets) * 100
            ratios['cash'] = (cash_investments / total_assets) * 100
            ratios['receivables'] = (accounts_receivable / total_assets) * 100
            ratios['npi'] = (abs(interest_income) / total_revenue) * 100

            passes['debt'] = bool(ratios['debt'] < 33.0)
            passes['cash'] = bool(ratios['cash'] < 33.0)
            passes['receivables'] = bool(ratios['receivables'] < 45.0)
            passes['npi'] = bool(ratios['npi'] < 5.0)

        report_data = generate_scholarly_report(name, sector, industry, is_haram_business, missing_data, ratios, passes)

        return {
            "Company_Profile": {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "industry": industry
            },
            **report_data,
            "Last_Updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
    except Exception as e:
        # Silently fail to not clutter the logs
        return None

def update_netherlands_stocks():
    tickers = get_netherlands_tickers()
    stock_data = []
    count = 0

    print("Starting Netherlands data extraction...")
    for ticker in tickers:
        count += 1
        if count % 200 == 0:
            print(f"Scanning progress: {count}/{len(tickers)}...")
            
        result = check_shariah_compliance(ticker)
        if result:
            stock_data.append(result)
        
        # Maintained your original Anti-ban sleep timing
        time.sleep(random.uniform(1.0, 2.5))

    # Saved entirely as a Netherlands specific JSON
    with open('netherlands_data.json', 'w') as f:
        json.dump(stock_data, f, indent=4, cls=NumpyEncoder)
        
    print(f"\n--- SUCCESS ---")
    print(f"Data saved: {len(stock_data)} valid Netherlands stocks processed successfully into netherlands_data.json.")

if __name__ == "__main__":
    update_netherlands_stocks()
