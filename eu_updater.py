import json
import time
import random
import requests
import yfinance as yf
import pandas as pd
import numpy as np

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

def fetch_wiki_tickers(url, suffix):
    tickers = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
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

def get_eu_tickers():
    eu_tickers = set()

    # 1. Fetch UK Stocks (LSE) - Completely Automated (~2000+ Stocks)
    try:
        print("Fetching official UK (LSE) stock list...")
        url = "https://raw.githubusercontent.com/ensbyp/Investor/master/Data/LSE.csv"
        df = pd.read_csv(url, on_bad_lines='skip')
        
        col = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
        for ticker in df[col].dropna().astype(str):
            clean_ticker = ticker.strip()
            if clean_ticker and clean_ticker.upper() != 'SYMBOL':
                if not clean_ticker.endswith(".L"):
                     eu_tickers.add(f"{clean_ticker}.L")
                else:
                     eu_tickers.add(clean_ticker)
        print("Successfully loaded LSE (UK) tickers.")
    except Exception as e:
        print(f"Error fetching LSE tickers: {e}")

    # 2. Fetch Major EU Indices via Wikipedia (Safe & Automated)
    wiki_sources = [
        ("https://en.wikipedia.org/wiki/DAX", "DE"),
        ("https://en.wikipedia.org/wiki/MDAX", "DE"),
        ("https://en.wikipedia.org/wiki/SDAX", "DE"),
        ("https://en.wikipedia.org/wiki/TecDAX", "DE"),
        ("https://en.wikipedia.org/wiki/CAC_40", "PA"),
        ("https://en.wikipedia.org/wiki/CAC_Next_20", "PA"),
        ("https://en.wikipedia.org/wiki/CAC_Mid_60", "PA"),
        ("https://en.wikipedia.org/wiki/FTSE_MIB", "MI"),
        ("https://en.wikipedia.org/wiki/IBEX_35", "MC"),
        ("https://en.wikipedia.org/wiki/AEX_index", "AS"),
        ("https://en.wikipedia.org/wiki/AMX_index", "AS"),
        ("https://en.wikipedia.org/wiki/BEL_20", "BR"),
        ("https://en.wikipedia.org/wiki/OMX_Stockholm_30", "ST"),
        ("https://en.wikipedia.org/wiki/OMX_Helsinki_25", "HE")
    ]
    
    print("Fetching major EU indices via Wikipedia...")
    for url, suffix in wiki_sources:
        fetched = fetch_wiki_tickers(url, suffix)
        eu_tickers.update(fetched)
        print(f"Loaded {len(fetched)} tickers from {suffix} index.")
        # Sleep to prevent Wikipedia blocking
        time.sleep(2)

    final_tickers = list(eu_tickers)
    print(f"Successfully compiled a total of {len(final_tickers)} unique EU/UK tickers.")
    
    # Fallback to prevent complete failure
    if len(final_tickers) < 10:
         return ["SHEL.L", "AZN.L", "HSBA.L", "SAP.DE", "MC.PA", "ASML.AS", "IBE.MC"]
    
    return final_tickers

def check_shariah_compliance(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('shortName', ticker)
        sector = info.get('sector', 'Unknown')

        bs = stock.balance_sheet
        fin = stock.financials

        if bs.empty or fin.empty:
            return None

        try:
            total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
            total_debt = bs.loc['Total Debt'].iloc[0] if 'Total Debt' in bs.index else 0
            
            cash = bs.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in bs.index else 0
            short_term_investments = bs.loc['Other Short Term Investments'].iloc[0] if 'Other Short Term Investments' in bs.index else 0
            total_cash_investments = cash + short_term_investments

            total_revenue = fin.loc['Total Revenue'].iloc[0] if 'Total Revenue' in fin.index else 0
            interest_income = fin.loc['Interest Income'].iloc[0] if 'Interest Income' in fin.index else 0
        except KeyError:
            return None

        # Handle missing essential data
        if total_assets == 0 or total_revenue == 0:
            return {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "status": "DOUBTFUL",
                "report": {
                    "debt_ratio": 0.0,
                    "cash_ratio": 0.0,
                    "income_ratio": 0.0,
                    "debt_pass": False,
                    "cash_pass": False,
                    "income_pass": False
                }
            }

        debt_ratio = (total_debt / total_assets) * 100
        cash_ratio = (total_cash_investments / total_assets) * 100
        income_ratio = (interest_income / total_revenue) * 100

        debt_pass = bool(debt_ratio < 33.0)
        cash_pass = bool(cash_ratio < 33.0)
        income_pass = bool(income_ratio < 5.0)

        # Fixed AAOIFI Shariah Logic
        if debt_pass and cash_pass and income_pass:
            status = "HALAL"
        else:
            status = "HARAM"

        return {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "status": status,
            "report": {
                "debt_ratio": round(float(debt_ratio), 2),
                "cash_ratio": round(float(cash_ratio), 2),
                "income_ratio": round(float(income_ratio), 2),
                "debt_pass": debt_pass,
                "cash_pass": cash_pass,
                "income_pass": income_pass
            }
        }
    except Exception:
        return None

def update_eu_stocks():
    tickers = get_eu_tickers()
    stock_data = []
    count = 0

    print("Starting EU data extraction...")
    for ticker in tickers:
        count += 1
        if count % 200 == 0:
            print(f"Scanning progress: {count}/{len(tickers)}...")
            
        result = check_shariah_compliance(ticker)
        if result:
            stock_data.append(result)
        
        # Anti-ban sleep for Yahoo Finance
        time.sleep(random.uniform(0.8, 1.8))

    with open('eu_data.json', 'w') as f:
        json.dump(stock_data, f, indent=4, cls=NumpyEncoder)
    print(f"Data saved: {len(stock_data)} valid EU/UK stocks processed successfully.")

if __name__ == "__main__":
    update_eu_stocks()
